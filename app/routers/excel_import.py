from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from sqlmodel import Session, select
from typing import List, Optional
import shutil
import tempfile
import os
import pandas as pd
from app.database import get_session
from app.models import User, Wallet, Category, Transaction
from app.auth import get_current_user
from app.excel_parser import parse_excel_file
from app.ai_service import parse_excel_with_gemini

router = APIRouter(prefix="/api/excel", tags=["Excel & CSV Import"])

class BulkImportItem(BaseModel):
    date: str
    description: str
    type: str  # INCOME or EXPENSE
    amount: float
    category_name: Optional[str] = None
    note: Optional[str] = ""

class BulkImportRequest(BaseModel):
    wallet_id: int
    transactions: List[BulkImportItem]

@router.post("/parse")
async def parse_uploaded_excel(
    file: UploadFile = File(...),
    use_ai: bool = Form(False),
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    filename = file.filename or "uploaded.xlsx"
    ext = os.path.splitext(filename)[1].lower()
    if ext not in [".xlsx", ".xls", ".csv"]:
        raise HTTPException(
            status_code=400,
            detail="Format berkas tidak didukung. Mohon unggah berkas .xlsx, .xls, atau .csv"
        )

    # Save to temp file
    with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
        shutil.copyfileobj(file.file, tmp)
        tmp_path = tmp.name

    try:
        # If user explicitly requested AI extraction or heuristic failed
        if use_ai:
            try:
                # Read sample lines / text representation of excel
                if ext == ".csv":
                    try:
                        df_sample = pd.read_csv(tmp_path, nrows=50)
                    except Exception:
                        df_sample = pd.read_csv(tmp_path, sep=";", nrows=50)
                else:
                    df_sample = pd.read_excel(tmp_path, nrows=50)

                raw_text = df_sample.to_string()
                ai_res = parse_excel_with_gemini(raw_text, session=session)
                if ai_res.get("success"):
                    return ai_res
                else:
                    # Fallback to heuristic parser if AI fails or key is missing
                    heuristic_res = parse_excel_file(tmp_path)
                    heuristic_res["ai_notice"] = ai_res.get("error")
                    return heuristic_res
            except Exception as e:
                # Fallback to standard parser
                return parse_excel_file(tmp_path)

        # Standard fast heuristic parser
        result = parse_excel_file(tmp_path)
        return result
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

@router.post("/confirm-import")
def confirm_import(
    req: BulkImportRequest,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    wallet = session.get(Wallet, req.wallet_id)
    if not wallet or wallet.user_id != current_user.id:
        raise HTTPException(status_code=400, detail="Akun kas tidak valid.")

    if not req.transactions:
        raise HTTPException(status_code=400, detail="Tidak ada transaksi untuk diimpor.")

    # Cache existing categories
    cats = session.exec(select(Category).where((Category.user_id == None) | (Category.user_id == current_user.id))).all()
    cat_map = {c.name.lower(): c.id for c in cats}

    saved_count = 0
    for item in req.transactions:
        if item.amount <= 0:
            continue

        cat_id = None
        if item.category_name:
            cat_name_clean = item.category_name.strip()
            cat_key = cat_name_clean.lower()
            if cat_key in cat_map:
                cat_id = cat_map[cat_key]
            else:
                # Create category dynamically for user
                new_cat = Category(
                    user_id=current_user.id,
                    name=cat_name_clean,
                    type=item.type.upper(),
                    color="#6366F1",
                    icon="tag"
                )
                session.add(new_cat)
                session.commit()
                session.refresh(new_cat)
                cat_map[cat_key] = new_cat.id
                cat_id = new_cat.id

        txn = Transaction(
            user_id=current_user.id,
            wallet_id=wallet.id,
            category_id=cat_id,
            type=item.type.upper(),
            amount=abs(item.amount),
            date=item.date,
            description=item.description,
            note=item.note or "Impor Excel"
        )
        session.add(txn)
        saved_count += 1

    session.commit()

    return {
        "success": True,
        "message": f"Berhasil mengimpor {saved_count} transaksi ke '{wallet.name}'!",
        "count": saved_count
    }
