from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlmodel import Session, select, func
from typing import Optional
from app.database import get_session
from app.models import User, Wallet, Category
from app.auth import hash_password, verify_password, create_access_token, get_current_user

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

class RegisterRequest(BaseModel):
    name: str
    email: EmailStr
    password: str

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class UpdateProfileRequest(BaseModel):
    name: Optional[str] = None
    current_password: Optional[str] = None
    new_password: Optional[str] = None

def init_default_user_data(user_id: int, session: Session):
    """Seed initial wallets and default categories for new user."""
    # Create default wallets
    default_wallets = [
        Wallet(user_id=user_id, name="Kas Tunai", type="CASH", initial_balance=0.0, color="#10B981", icon="banknote"),
        Wallet(user_id=user_id, name="Rekening Bank", type="BANK", initial_balance=0.0, color="#3B82F6", icon="landmark"),
        Wallet(user_id=user_id, name="Dompet Digital", type="EWALLET", initial_balance=0.0, color="#8B5CF6", icon="smartphone"),
    ]
    for w in default_wallets:
        session.add(w)

    session.commit()

@router.post("/register")
def register(req: RegisterRequest, session: Session = Depends(get_session)):
    # Check if email already registered
    existing_user = session.exec(select(User).where(User.email == req.email.lower())).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email sudah terdaftar. Silakan gunakan email lain atau login."
        )

    # First user registered in the system becomes ADMIN automatically!
    user_count = session.exec(select(func.count(User.id))).one()
    role = "ADMIN" if user_count == 0 else "USER"

    new_user = User(
        name=req.name.strip(),
        email=req.email.lower().strip(),
        password_hash=hash_password(req.password),
        role=role,
        is_active=True
    )
    session.add(new_user)
    session.commit()
    session.refresh(new_user)

    # Seed default wallets
    init_default_user_data(new_user.id, session)

    token = create_access_token(data={"sub": str(new_user.id), "email": new_user.email, "role": new_user.role})

    return {
        "success": True,
        "message": f"Pendaftaran berhasil! Peran Anda: {new_user.role}",
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": new_user.id,
            "name": new_user.name,
            "email": new_user.email,
            "role": new_user.role
        }
    }

@router.post("/login")
def login(req: LoginRequest, session: Session = Depends(get_session)):
    user = session.exec(select(User).where(User.email == req.email.lower())).first()
    if not user or not verify_password(req.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email atau kata sandi tidak cocok."
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Akun Anda dinonaktifkan oleh Administrator."
        )

    token = create_access_token(data={"sub": str(user.id), "email": user.email, "role": user.role})

    return {
        "success": True,
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "role": user.role
        }
    }

@router.get("/me")
def get_profile(current_user: User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "name": current_user.name,
        "email": current_user.email,
        "role": current_user.role,
        "is_active": current_user.is_active,
        "created_at": current_user.created_at.isoformat()
    }

@router.put("/profile")
def update_profile(
    req: UpdateProfileRequest,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    if req.name:
        current_user.name = req.name.strip()

    if req.new_password:
        if not req.current_password or not verify_password(req.current_password, current_user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Kata sandi saat ini tidak cocok."
            )
        if len(req.new_password) < 6:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Kata sandi baru minimal 6 karakter."
            )
        current_user.password_hash = hash_password(req.new_password)

    session.add(current_user)
    session.commit()
    session.refresh(current_user)

    return {"success": True, "message": "Profil berhasil diperbarui", "name": current_user.name}
