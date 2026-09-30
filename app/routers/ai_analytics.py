from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlmodel import Session, select
from typing import List, Dict, Any, Optional
from datetime import datetime
from app.database import get_session
from app.models import User, Wallet, Category, Transaction
from app.auth import get_current_user
from app.ai_service import analyze_financial_health_with_gemini, chat_with_financial_ai
from app.routers.wallets import calculate_wallet_balance

router = APIRouter(prefix="/api/ai", tags=["AI Analytics & Assistant"])

class ChatMessage(BaseModel):
    role: str  # user or model
    content: str

class ChatRequest(BaseModel):
    message: str
    history: List[ChatMessage] = []

def build_financial_context(current_user: User, session: Session) -> Dict[str, Any]:
    if current_user.role == "ADMIN":
        wallets = session.exec(select(Wallet).where(Wallet.is_active == True)).all()
        txns = session.exec(select(Transaction).order_by(Transaction.date.desc())).all()
    else:
        wallets = session.exec(select(Wallet).where(Wallet.user_id == current_user.id, Wallet.is_active == True)).all()
        txns = session.exec(select(Transaction).where(Transaction.user_id == current_user.id).order_by(Transaction.date.desc())).all()

    wallet_summaries = []
    total_balance = 0.0
    for w in wallets:
        bal = calculate_wallet_balance(w, session)
        total_balance += bal
        wallet_summaries.append({"name": w.name, "type": w.type, "balance": bal})

    total_income = sum(t.amount for t in txns if t.type == "INCOME")
    total_expense = sum(t.amount for t in txns if t.type == "EXPENSE")
    net_cashflow = total_income - total_expense

    categories = {c.id: c.name for c in session.exec(select(Category)).all()}
    expense_by_cat = {}
    income_by_cat = {}
    recent_txns = []

    for idx, t in enumerate(txns):
        cat_name = categories.get(t.category_id, "Lain-lain") if t.category_id else "Tanpa Kategori"
        if t.type == "EXPENSE":
            expense_by_cat[cat_name] = expense_by_cat.get(cat_name, 0.0) + t.amount
        elif t.type == "INCOME":
            income_by_cat[cat_name] = income_by_cat.get(cat_name, 0.0) + t.amount

        if idx < 20:
            recent_txns.append({
                "date": t.date,
                "type": t.type,
                "amount": t.amount,
                "category": cat_name,
                "description": t.description
            })

    return {
        "current_balance": total_balance,
        "total_income": total_income,
        "total_expense": total_expense,
        "net_cashflow": net_cashflow,
        "wallets": wallet_summaries,
        "expense_by_category": expense_by_cat,
        "income_by_category": income_by_cat,
        "recent_transactions": recent_txns
    }

@router.get("/health-check")
def financial_health_check(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    ctx = build_financial_context(current_user, session)
    analysis = analyze_financial_health_with_gemini(
        summary_data=ctx,
        recent_transactions=ctx.get("recent_transactions", []),
        session=session
    )
    return {
        "success": True,
        "analysis": analysis,
        "metrics": {
            "balance": ctx["current_balance"],
            "income": ctx["total_income"],
            "expense": ctx["total_expense"],
            "net": ctx["net_cashflow"]
        }
    }

@router.post("/chat")
def ai_financial_chat(
    req: ChatRequest,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    if not req.message.strip():
        raise HTTPException(status_code=400, detail="Pesan tidak boleh kosong.")

    ctx = build_financial_context(current_user, session)
    history_dicts = [{"role": m.role, "content": m.content} for m in req.history]

    reply = chat_with_financial_ai(
        user_message=req.message,
        chat_history=history_dicts,
        financial_context=ctx,
        session=session
    )

    return {
        "success": True,
        "reply": reply
    }
