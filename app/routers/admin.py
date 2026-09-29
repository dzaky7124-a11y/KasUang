import json
import io
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, EmailStr
from sqlmodel import Session, select, func
from typing import Optional, List
from datetime import datetime
from app.database import get_session
from app.models import User, Wallet, Category, Transaction, SystemConfig
from app.auth import get_current_admin_user, hash_password
from app.routers.auth import init_default_user_data

router = APIRouter(prefix="/api/admin", tags=["Admin Management"])

class AdminUserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str
    role: str = "USER"  # ADMIN or USER

class AdminResetPassword(BaseModel):
    new_password: str

class AdminRoleUpdate(BaseModel):
    role: str  # ADMIN or USER

class SystemConfigUpdate(BaseModel):
    gemini_api_key: Optional[str] = None
    app_name: Optional[str] = None

@router.get("/users")
def get_all_users(admin: User = Depends(get_current_admin_user), session: Session = Depends(get_session)):
    users = session.exec(select(User).order_by(User.id)).all()
    results = []
    for u in users:
        wallet_count = session.exec(select(func.count(Wallet.id)).where(Wallet.user_id == u.id, Wallet.is_active == True)).one()
        txn_count = session.exec(select(func.count(Transaction.id)).where(Transaction.user_id == u.id)).one()
        results.append({
            "id": u.id,
            "name": u.name,
            "email": u.email,
            "role": u.role,
            "is_active": u.is_active,
            "wallet_count": wallet_count,
            "transaction_count": txn_count,
            "created_at": u.created_at.isoformat()
        })
    return {"users": results}

@router.post("/users")
def create_user_by_admin(
    req: AdminUserCreate,
    admin: User = Depends(get_current_admin_user),
    session: Session = Depends(get_session)
):
    existing = session.exec(select(User).where(User.email == req.email.lower())).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email sudah digunakan.")

    new_user = User(
        name=req.name.strip(),
        email=req.email.lower().strip(),
        password_hash=hash_password(req.password),
        role=req.role.upper(),
        is_active=True
    )
    session.add(new_user)
    session.commit()
    session.refresh(new_user)

    init_default_user_data(new_user.id, session)

    return {"success": True, "message": f"Pengguna {new_user.name} berhasil dibuat."}

@router.put("/users/{user_id}/toggle-status")
def toggle_user_status(
    user_id: int,
    admin: User = Depends(get_current_admin_user),
    session: Session = Depends(get_session)
):
    if user_id == admin.id:
        raise HTTPException(status_code=400, detail="Tidak dapat menonaktifkan akun Anda sendiri.")

    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Pengguna tidak ditemukan.")

    user.is_active = not user.is_active
    session.add(user)
    session.commit()

    status_str = "diaktifkan" if user.is_active else "dinonaktifkan"
    return {"success": True, "message": f"Akun pengguna berhasil {status_str}.", "is_active": user.is_active}

@router.put("/users/{user_id}/role")
def change_user_role(
    user_id: int,
    req: AdminRoleUpdate,
    admin: User = Depends(get_current_admin_user),
    session: Session = Depends(get_session)
):
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Pengguna tidak ditemukan.")

    if user_id == admin.id and req.role.upper() != "ADMIN":
        # Check if there is another admin
        admin_count = session.exec(select(func.count(User.id)).where(User.role == "ADMIN", User.is_active == True)).one()
        if admin_count <= 1:
            raise HTTPException(status_code=400, detail="Tidak dapat mengubah role admin terakhir dalam sistem.")

    user.role = req.role.upper()
    session.add(user)
    session.commit()

    return {"success": True, "message": f"Peran pengguna berhasil diubah menjadi {user.role}."}

@router.put("/users/{user_id}/reset-password")
def reset_user_password(
    user_id: int,
    req: AdminResetPassword,
    admin: User = Depends(get_current_admin_user),
    session: Session = Depends(get_session)
):
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Pengguna tidak ditemukan.")

    if len(req.new_password) < 6:
        raise HTTPException(status_code=400, detail="Kata sandi baru minimal 6 karakter.")

    user.password_hash = hash_password(req.new_password)
    session.add(user)
    session.commit()

    return {"success": True, "message": f"Kata sandi untuk {user.email} berhasil direset."}

@router.get("/system-stats")
def get_system_stats(admin: User = Depends(get_current_admin_user), session: Session = Depends(get_session)):
    total_users = session.exec(select(func.count(User.id))).one()
    active_users = session.exec(select(func.count(User.id)).where(User.is_active == True)).one()
    total_wallets = session.exec(select(func.count(Wallet.id)).where(Wallet.is_active == True)).one()
    total_txns = session.exec(select(func.count(Transaction.id))).one()
    total_volume = session.exec(select(func.coalesce(func.sum(Transaction.amount), 0.0))).one()

    return {
        "total_users": total_users,
        "active_users": active_users,
        "total_wallets": total_wallets,
        "total_transactions": total_txns,
        "total_volume": total_volume
    }

@router.get("/config")
def get_system_config(admin: User = Depends(get_current_admin_user), session: Session = Depends(get_session)):
    gemini_key = session.exec(select(SystemConfig).where(SystemConfig.key == "GEMINI_API_KEY")).first()
    key_val = gemini_key.value if gemini_key else ""
    
    # Obfuscate key for security preview
    masked_key = f"{key_val[:4]}...{key_val[-4:]}" if len(key_val) > 8 else ("Dikonfigurasi" if key_val else "Belum Dikonfigurasi")
    
    return {
        "gemini_api_key_configured": bool(key_val),
        "gemini_api_key_preview": masked_key,
        "has_key": bool(key_val)
    }

@router.post("/config")
def update_system_config(
    req: SystemConfigUpdate,
    admin: User = Depends(get_current_admin_user),
    session: Session = Depends(get_session)
):
    if req.gemini_api_key is not None:
        key_entry = session.exec(select(SystemConfig).where(SystemConfig.key == "GEMINI_API_KEY")).first()
        if not key_entry:
            key_entry = SystemConfig(key="GEMINI_API_KEY", value=req.gemini_api_key.strip(), description="Google Gemini API Key")
        else:
            key_entry.value = req.gemini_api_key.strip()
            key_entry.updated_at = datetime.utcnow()
        session.add(key_entry)
        session.commit()

    return {"success": True, "message": "Konfigurasi sistem berhasil diperbarui."}

@router.get("/backup-db")
def export_backup_json(admin: User = Depends(get_current_admin_user), session: Session = Depends(get_session)):
    """Exports full database records to JSON for easy cloud backup."""
    users = session.exec(select(User)).all()
    wallets = session.exec(select(Wallet)).all()
    categories = session.exec(select(Category)).all()
    txns = session.exec(select(Transaction)).all()

    backup_payload = {
        "version": "1.0",
        "exported_at": datetime.utcnow().isoformat(),
        "users": [{"id": u.id, "name": u.name, "email": u.email, "role": u.role, "password_hash": u.password_hash, "is_active": u.is_active} for u in users],
        "wallets": [{"id": w.id, "user_id": w.user_id, "name": w.name, "type": w.type, "initial_balance": w.initial_balance, "color": w.color, "icon": w.icon, "is_active": w.is_active} for w in wallets],
        "categories": [{"id": c.id, "user_id": c.user_id, "name": c.name, "type": c.type, "icon": c.icon, "color": c.color} for c in categories],
        "transactions": [{"id": t.id, "user_id": t.user_id, "wallet_id": t.wallet_id, "category_id": t.category_id, "type": t.type, "amount": t.amount, "date": t.date, "description": t.description, "note": t.note, "transfer_wallet_id": t.transfer_wallet_id} for t in txns]
    }

    stream = io.StringIO(json.dumps(backup_payload, indent=2))
    response = StreamingResponse(iter([stream.getvalue()]), media_type="application/json")
    response.headers["Content-Disposition"] = f"attachment; filename=backup_kaspintar_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
    return response

@router.post("/restore-db")
async def restore_backup_json(
    file: UploadFile = File(...),
    admin: User = Depends(get_current_admin_user),
    session: Session = Depends(get_session)
):
    try:
        content = await file.read()
        data = json.loads(content.decode("utf-8"))

        if "transactions" not in data or "users" not in data:
            raise HTTPException(status_code=400, detail="Format berkas cadangan JSON tidak valid.")

        # Restore process (upsert users, wallets, categories, transactions)
        for u in data.get("users", []):
            existing = session.get(User, u["id"])
            if not existing:
                session.add(User(**u))

        for w in data.get("wallets", []):
            existing = session.get(Wallet, w["id"])
            if not existing:
                session.add(Wallet(**w))

        for c in data.get("categories", []):
            existing = session.get(Category, c["id"])
            if not existing:
                session.add(Category(**c))

        for t in data.get("transactions", []):
            existing = session.get(Transaction, t["id"])
            if not existing:
                session.add(Transaction(**t))

        session.commit()
        return {"success": True, "message": "Pemulihan data cadangan berhasil disinkronkan!"}
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=400, detail=f"Gagal memulihkan cadangan: {str(e)}")
