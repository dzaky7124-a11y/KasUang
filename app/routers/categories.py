from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlmodel import Session, select
from typing import Optional, List
from app.database import get_session
from app.models import User, Category
from app.auth import get_current_user

router = APIRouter(prefix="/api/categories", tags=["Categories"])

class CategoryCreate(BaseModel):
    name: str
    type: str = "EXPENSE"  # INCOME or EXPENSE
    icon: str = "tag"
    color: str = "#6B7280"

DEFAULT_CATEGORIES = [
    # INCOME
    {"name": "Penjualan & Omset", "type": "INCOME", "icon": "shopping-bag", "color": "#10B981"},
    {"name": "Gaji & Upah", "type": "INCOME", "icon": "banknote", "color": "#059669"},
    {"name": "Investasi & Bunga", "type": "INCOME", "icon": "trending-up", "color": "#3B82F6"},
    {"name": "Bonus & Komisi", "type": "INCOME", "icon": "award", "color": "#F59E0B"},
    {"name": "Pengembalian Dana", "type": "INCOME", "icon": "rotate-ccw", "color": "#6366F1"},
    {"name": "Pemasukan Lainnya", "type": "INCOME", "icon": "plus-circle", "color": "#84CC16"},
    # EXPENSE
    {"name": "Makanan & Minuman", "type": "EXPENSE", "icon": "utensils", "color": "#EF4444"},
    {"name": "Transportasi & Bensin", "type": "EXPENSE", "icon": "car", "color": "#F97316"},
    {"name": "Tagihan & Utilitas", "type": "EXPENSE", "icon": "zap", "color": "#EAB308"},
    {"name": "Belanja Stok & Bahan", "type": "EXPENSE", "icon": "package", "color": "#8B5CF6"},
    {"name": "Gaji Karyawan", "type": "EXPENSE", "icon": "users", "color": "#EC4899"},
    {"name": "Sewa Tempat", "type": "EXPENSE", "icon": "home", "color": "#14B8A6"},
    {"name": "Pemasaran & Iklan", "type": "EXPENSE", "icon": "megaphone", "color": "#06B6D4"},
    {"name": "Pemeliharaan & Servis", "type": "EXPENSE", "icon": "wrench", "color": "#64748B"},
    {"name": "Pengeluaran Operasional", "type": "EXPENSE", "icon": "briefcase", "color": "#DC2626"},
    {"name": "Pengeluaran Lainnya", "type": "EXPENSE", "icon": "minus-circle", "color": "#9CA3AF"}
]

def ensure_default_categories(session: Session):
    existing = session.exec(select(Category).where(Category.user_id == None)).first()
    if not existing:
        for c in DEFAULT_CATEGORIES:
            cat = Category(
                user_id=None,
                name=c["name"],
                type=c["type"],
                icon=c["icon"],
                color=c["color"]
            )
            session.add(cat)
        session.commit()

@router.get("")
def list_categories(current_user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    ensure_default_categories(session)
    
    cats = session.exec(
        select(Category).where(
            (Category.user_id == None) | (Category.user_id == current_user.id)
        ).order_by(Category.name)
    ).all()

    income_cats = [c for c in cats if c.type == "INCOME"]
    expense_cats = [c for c in cats if c.type == "EXPENSE"]

    return {
        "categories": cats,
        "income": income_cats,
        "expense": expense_cats
    }

@router.post("")
def create_category(req: CategoryCreate, current_user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    new_cat = Category(
        user_id=current_user.id,
        name=req.name.strip(),
        type=req.type.upper(),
        icon=req.icon,
        color=req.color
    )
    session.add(new_cat)
    session.commit()
    session.refresh(new_cat)
    return {"success": True, "category": new_cat}

@router.delete("/{cat_id}")
def delete_category(cat_id: int, current_user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    cat = session.get(Category, cat_id)
    if not cat:
        raise HTTPException(status_code=404, detail="Kategori tidak ditemukan.")
    if cat.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Tidak dapat menghapus kategori bawaan sistem.")

    session.delete(cat)
    session.commit()
    return {"success": True, "message": "Kategori berhasil dihapus."}
