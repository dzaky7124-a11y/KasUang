from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlmodel import Session, select, func
from typing import List, Optional
from app.database import get_session
from app.models import User, Wallet, Transaction
from app.auth import get_current_user

router = APIRouter(prefix="/api/wallets", tags=["Wallets / Akun Kas"])

class WalletCreate(BaseModel):
    name: str
    type: str = "CASH"  # CASH, BANK, EWALLET, OTHER
    initial_balance: float = 0.0
    color: str = "#10B981"
    icon: str = "wallet"

class WalletUpdate(BaseModel):
    name: Optional[str] = None
    type: Optional[str] = None
    initial_balance: Optional[float] = None
    color: Optional[str] = None
    icon: Optional[str] = None
    is_active: Optional[bool] = None

def calculate_wallet_balance(wallet: Wallet, session: Session) -> float:
    # Sum Income
    income = session.exec(
        select(func.coalesce(func.sum(Transaction.amount), 0.0))
        .where(Transaction.wallet_id == wallet.id, Transaction.type == "INCOME")
    ).one()

    # Sum Expense
    expense = session.exec(
        select(func.coalesce(func.sum(Transaction.amount), 0.0))
        .where(Transaction.wallet_id == wallet.id, Transaction.type == "EXPENSE")
    ).one()

    # Sum Transfer Out
    transfer_out = session.exec(
        select(func.coalesce(func.sum(Transaction.amount), 0.0))
        .where(Transaction.wallet_id == wallet.id, Transaction.type == "TRANSFER")
    ).one()

    # Sum Transfer In
    transfer_in = session.exec(
        select(func.coalesce(func.sum(Transaction.amount), 0.0))
        .where(Transaction.transfer_wallet_id == wallet.id, Transaction.type == "TRANSFER")
    ).one()

    return wallet.initial_balance + income - expense - transfer_out + transfer_in

@router.get("")
def list_wallets(current_user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    wallets = session.exec(
        select(Wallet).where(Wallet.user_id == current_user.id, Wallet.is_active == True)
    ).all()

    result = []
    total_balance = 0.0
    for w in wallets:
        bal = calculate_wallet_balance(w, session)
        total_balance += bal
        result.append({
            "id": w.id,
            "name": w.name,
            "type": w.type,
            "initial_balance": w.initial_balance,
            "current_balance": bal,
            "color": w.color,
            "icon": w.icon,
            "created_at": w.created_at.isoformat()
        })

    return {
        "wallets": result,
        "total_balance": total_balance
    }

@router.post("")
def create_wallet(req: WalletCreate, current_user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    new_wallet = Wallet(
        user_id=current_user.id,
        name=req.name.strip(),
        type=req.type.upper(),
        initial_balance=req.initial_balance,
        color=req.color,
        icon=req.icon
    )
    session.add(new_wallet)
    session.commit()
    session.refresh(new_wallet)

    return {
        "success": True,
        "wallet": {
            "id": new_wallet.id,
            "name": new_wallet.name,
            "type": new_wallet.type,
            "initial_balance": new_wallet.initial_balance,
            "current_balance": new_wallet.initial_balance,
            "color": new_wallet.color,
            "icon": new_wallet.icon
        }
    }

@router.put("/{wallet_id}")
def update_wallet(wallet_id: int, req: WalletUpdate, current_user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    wallet = session.get(Wallet, wallet_id)
    if not wallet or wallet.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Akun kas tidak ditemukan.")

    if req.name is not None:
        wallet.name = req.name.strip()
    if req.type is not None:
        wallet.type = req.type.upper()
    if req.initial_balance is not None:
        wallet.initial_balance = req.initial_balance
    if req.color is not None:
        wallet.color = req.color
    if req.icon is not None:
        wallet.icon = req.icon
    if req.is_active is not None:
        wallet.is_active = req.is_active

    session.add(wallet)
    session.commit()
    session.refresh(wallet)

    return {"success": True, "message": "Akun kas berhasil diperbarui."}

@router.delete("/{wallet_id}")
def delete_wallet(wallet_id: int, current_user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    wallet = session.get(Wallet, wallet_id)
    if not wallet or wallet.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Akun kas tidak ditemukan.")

    # Soft delete
    wallet.is_active = False
    session.add(wallet)
    session.commit()

    return {"success": True, "message": "Akun kas berhasil dihapus."}
