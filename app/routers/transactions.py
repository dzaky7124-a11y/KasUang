from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlmodel import Session, select, func, and_, or_
from typing import Optional, List
from datetime import datetime, date, timedelta
import io
import pandas as pd
from app.database import get_session
from app.models import User, Wallet, Category, Transaction
from app.auth import get_current_user

router = APIRouter(prefix="/api/transactions", tags=["Transactions"])

class TransactionCreate(BaseModel):
    wallet_id: int
    category_id: Optional[int] = None
    type: str  # INCOME, EXPENSE, TRANSFER
    amount: float
    date: str  # YYYY-MM-DD
    description: str
    note: Optional[str] = ""
    transfer_wallet_id: Optional[int] = None

class TransactionUpdate(BaseModel):
    wallet_id: Optional[int] = None
    category_id: Optional[int] = None
    type: Optional[str] = None
    amount: Optional[float] = None
    date: Optional[str] = None
    description: Optional[str] = None
    note: Optional[str] = None
    transfer_wallet_id: Optional[int] = None

@router.get("")
def list_transactions(
    wallet_id: Optional[int] = Query(None),
    category_id: Optional[int] = Query(None),
    type: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(25, ge=1, le=200),
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    query = select(Transaction).where(Transaction.user_id == current_user.id)

    if wallet_id:
        query = query.where(
            or_(
                Transaction.wallet_id == wallet_id,
                Transaction.transfer_wallet_id == wallet_id
            )
        )
    if category_id:
        query = query.where(Transaction.category_id == category_id)
    if type:
        query = query.where(Transaction.type == type.upper())
    if start_date:
        query = query.where(Transaction.date >= start_date)
    if end_date:
        query = query.where(Transaction.date <= end_date)
    if search:
        search_fmt = f"%{search.strip()}%"
        query = query.where(
            or_(
                Transaction.description.ilike(search_fmt),
                Transaction.note.ilike(search_fmt)
            )
        )

    # Order by date descending, then created_at descending
    query = query.order_by(Transaction.date.desc(), Transaction.id.desc())

    # Count total matching
    total_query = select(func.count()).select_from(query.subquery())
    total_count = session.exec(total_query).one()

    # Pagination
    offset = (page - 1) * limit
    paginated_query = query.offset(offset).limit(limit)
    txns = session.exec(paginated_query).all()

    # Pre-fetch wallets and categories map for fast response
    user_wallets = {w.id: w for w in session.exec(select(Wallet).where(Wallet.user_id == current_user.id)).all()}
    categories = {c.id: c for c in session.exec(select(Category)).all()}

    items = []
    for t in txns:
        w = user_wallets.get(t.wallet_id)
        tw = user_wallets.get(t.transfer_wallet_id) if t.transfer_wallet_id else None
        c = categories.get(t.category_id) if t.category_id else None
        items.append({
            "id": t.id,
            "type": t.type,
            "amount": t.amount,
            "date": t.date,
            "description": t.description,
            "note": t.note or "",
            "wallet": {"id": w.id, "name": w.name, "color": w.color} if w else None,
            "transfer_wallet": {"id": tw.id, "name": tw.name, "color": tw.color} if tw else None,
            "category": {"id": c.id, "name": c.name, "color": c.color, "icon": c.icon} if c else None,
            "created_at": t.created_at.isoformat()
        })

    return {
        "items": items,
        "total": total_count,
        "page": page,
        "limit": limit,
        "total_pages": (total_count + limit - 1) // limit if total_count > 0 else 1
    }

@router.post("")
def create_transaction(
    req: TransactionCreate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    # Verify wallet belongs to user
    wallet = session.get(Wallet, req.wallet_id)
    if not wallet or wallet.user_id != current_user.id:
        raise HTTPException(status_code=400, detail="Akun kas tidak valid.")

    if req.type == "TRANSFER":
        if not req.transfer_wallet_id or req.transfer_wallet_id == req.wallet_id:
            raise HTTPException(status_code=400, detail="Pilih akun kas tujuan transfer yang berbeda.")
        target_wallet = session.get(Wallet, req.transfer_wallet_id)
        if not target_wallet or target_wallet.user_id != current_user.id:
            raise HTTPException(status_code=400, detail="Akun kas tujuan transfer tidak valid.")

    new_txn = Transaction(
        user_id=current_user.id,
        wallet_id=req.wallet_id,
        category_id=req.category_id,
        type=req.type.upper(),
        amount=abs(req.amount),
        date=req.date,
        description=req.description.strip(),
        note=req.note.strip() if req.note else "",
        transfer_wallet_id=req.transfer_wallet_id if req.type == "TRANSFER" else None
    )
    session.add(new_txn)
    session.commit()
    session.refresh(new_txn)

    return {"success": True, "message": "Transaksi berhasil disimpan", "id": new_txn.id}

@router.put("/{txn_id}")
def update_transaction(
    txn_id: int,
    req: TransactionUpdate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    txn = session.get(Transaction, txn_id)
    if not txn or txn.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Transaksi tidak ditemukan.")

    if req.wallet_id is not None:
        wallet = session.get(Wallet, req.wallet_id)
        if not wallet or wallet.user_id != current_user.id:
            raise HTTPException(status_code=400, detail="Akun kas tidak valid.")
        txn.wallet_id = req.wallet_id

    if req.category_id is not None:
        txn.category_id = req.category_id
    if req.type is not None:
        txn.type = req.type.upper()
    if req.amount is not None:
        txn.amount = abs(req.amount)
    if req.date is not None:
        txn.date = req.date
    if req.description is not None:
        txn.description = req.description.strip()
    if req.note is not None:
        txn.note = req.note.strip()
    if req.transfer_wallet_id is not None:
        txn.transfer_wallet_id = req.transfer_wallet_id

    session.add(txn)
    session.commit()
    return {"success": True, "message": "Transaksi berhasil diperbarui"}

@router.delete("/{txn_id}")
def delete_transaction(
    txn_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    txn = session.get(Transaction, txn_id)
    if not txn or txn.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Transaksi tidak ditemukan.")

    session.delete(txn)
    session.commit()
    return {"success": True, "message": "Transaksi berhasil dihapus"}

@router.get("/summary")
def get_summary(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    wallet_id: Optional[int] = Query(None),
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    base_query = select(Transaction).where(Transaction.user_id == current_user.id)
    if start_date:
        base_query = base_query.where(Transaction.date >= start_date)
    if end_date:
        base_query = base_query.where(Transaction.date <= end_date)
    if wallet_id:
        base_query = base_query.where(
            or_(
                Transaction.wallet_id == wallet_id,
                Transaction.transfer_wallet_id == wallet_id
            )
        )

    txns = session.exec(base_query).all()

    total_income = sum(t.amount for t in txns if t.type == "INCOME")
    total_expense = sum(t.amount for t in txns if t.type == "EXPENSE")
    net_cashflow = total_income - total_expense

    # Expense by category
    categories = {c.id: c.name for c in session.exec(select(Category)).all()}
    expense_by_cat = {}
    income_by_cat = {}

    for t in txns:
        cat_name = categories.get(t.category_id, "Lain-lain") if t.category_id else "Tanpa Kategori"
        if t.type == "EXPENSE":
            expense_by_cat[cat_name] = expense_by_cat.get(cat_name, 0.0) + t.amount
        elif t.type == "INCOME":
            income_by_cat[cat_name] = income_by_cat.get(cat_name, 0.0) + t.amount

    # Daily trends (last 30 days or filtered range)
    trend_dict = {}
    for t in txns:
        d = t.date
        if d not in trend_dict:
            trend_dict[d] = {"date": d, "income": 0.0, "expense": 0.0}
        if t.type == "INCOME":
            trend_dict[d]["income"] += t.amount
        elif t.type == "EXPENSE":
            trend_dict[d]["expense"] += t.amount

    sorted_trends = sorted(trend_dict.values(), key=lambda x: x["date"])

    # Calculate total current balance across all user wallets
    from app.routers.wallets import calculate_wallet_balance
    user_wallets = session.exec(select(Wallet).where(Wallet.user_id == current_user.id, Wallet.is_active == True)).all()
    total_wallet_balance = sum(calculate_wallet_balance(w, session) for w in user_wallets)

    return {
        "total_income": total_income,
        "total_expense": total_expense,
        "net_cashflow": net_cashflow,
        "total_balance": total_wallet_balance,
        "total_transactions": len(txns),
        "expense_by_category": expense_by_cat,
        "income_by_category": income_by_cat,
        "daily_trends": sorted_trends
    }

@router.get("/export")
def export_transactions(
    format: str = Query("xlsx", pattern="^(xlsx|csv)$"),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    wallet_id: Optional[int] = Query(None),
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    query = select(Transaction).where(Transaction.user_id == current_user.id)
    if start_date:
        query = query.where(Transaction.date >= start_date)
    if end_date:
        query = query.where(Transaction.date <= end_date)
    if wallet_id:
        query = query.where(
            or_(
                Transaction.wallet_id == wallet_id,
                Transaction.transfer_wallet_id == wallet_id
            )
        )

    txns = session.exec(query.order_by(Transaction.date.desc())).all()
    user_wallets = {w.id: w.name for w in session.exec(select(Wallet).where(Wallet.user_id == current_user.id)).all()}
    categories = {c.id: c.name for c in session.exec(select(Category)).all()}

    rows = []
    for t in txns:
        w_name = user_wallets.get(t.wallet_id, "Kas")
        c_name = categories.get(t.category_id, "-") if t.category_id else "-"
        type_label = "Pemasukan" if t.type == "INCOME" else ("Pengeluaran" if t.type == "EXPENSE" else "Transfer")
        rows.append({
            "Tanggal": t.date,
            "Akun Kas": w_name,
            "Tipe": type_label,
            "Kategori": c_name,
            "Keterangan": t.description,
            "Nominal (Rp)": t.amount,
            "Catatan": t.note or ""
        })

    df = pd.DataFrame(rows)

    if format == "csv":
        stream = io.StringIO()
        df.to_csv(stream, index=False, sep=";")
        response = StreamingResponse(
            iter([stream.getvalue()]),
            media_type="text/csv"
        )
        response.headers["Content-Disposition"] = "attachment; filename=laporan_kas.csv"
        return response
    else:
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="Laporan Kas")
        output.seek(0)
        response = StreamingResponse(
            output,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        response.headers["Content-Disposition"] = "attachment; filename=laporan_kas.xlsx"
        return response
