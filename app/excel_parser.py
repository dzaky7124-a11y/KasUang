import re
import pandas as pd
from datetime import datetime
from typing import List, Dict, Any, Optional

def clean_amount(val: Any) -> float:
    if val is None or pd.isna(val):
        return 0.0
    if isinstance(val, (int, float)):
        return float(val)
    
    val_str = str(val).strip()
    if not val_str:
        return 0.0
    
    is_negative = False
    if val_str.startswith("(") and val_str.endswith(")"):
        is_negative = True
        val_str = val_str[1:-1].strip()
    elif val_str.startswith("-"):
        is_negative = True
        val_str = val_str[1:].strip()
        
    val_str = re.sub(r"[^\d.,]", "", val_str)
    if not val_str:
        return 0.0
    
    # Handle Indonesian format: 1.500.000,00 -> 1500000.00
    # or US format: 1,500,000.00 -> 1500000.00
    if "." in val_str and "," in val_str:
        if val_str.rfind(",") > val_str.rfind("."):
            val_str = val_str.replace(".", "").replace(",", ".")
        else:
            val_str = val_str.replace(",", "")
    elif "," in val_str:
        parts = val_str.split(",")
        if len(parts) == 2 and len(parts[1]) <= 2:
            val_str = parts[0] + "." + parts[1]
        else:
            val_str = val_str.replace(",", "")
    elif "." in val_str:
        parts = val_str.split(".")
        if len(parts) > 2 or (len(parts) == 2 and len(parts[1]) == 3 and int(parts[0]) > 0):
            val_str = "".join(parts)
            
    try:
        amount = float(val_str)
        return -amount if is_negative else amount
    except ValueError:
        return 0.0

def parse_date_str(val: Any) -> str:
    if val is None or pd.isna(val):
        return datetime.now().strftime("%Y-%m-%d")
    
    if isinstance(val, (datetime, pd.Timestamp)):
        return val.strftime("%Y-%m-%d")
        
    val_str = str(val).strip()
    formats = [
        "%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%m/%d/%Y",
        "%Y/%m/%d", "%d.%m.%Y", "%Y.%m.%d",
        "%d %B %Y", "%d %b %Y", "%d-%b-%Y", "%d-%b-%y"
    ]
    for fmt in formats:
        try:
            return datetime.strptime(val_str, fmt).strftime("%Y-%m-%d")
        except Exception:
            pass

    match = re.search(r"(\d{4})[-/.](\d{1,2})[-/.](\d{1,2})", val_str)
    if match:
        y, m, d = match.groups()
        return f"{int(y):04d}-{int(m):02d}-{int(d):02d}"
        
    match2 = re.search(r"(\d{1,2})[-/.](\d{1,2})[-/.](\d{2,4})", val_str)
    if match2:
        d, m, y = match2.groups()
        if len(y) == 2:
            y = "20" + y
        return f"{int(y):04d}-{int(m):02d}-{int(d):02d}"

    return datetime.now().strftime("%Y-%m-%d")

def match_col_keyword(col_name: str, keywords: List[str]) -> bool:
    clean = str(col_name).strip().lower()
    words = re.findall(r"[a-z0-9]+", clean)
    for kw in keywords:
        kw_clean = kw.lower()
        if kw_clean == clean or kw_clean in words:
            return True
        if len(kw_clean) >= 4 and kw_clean in clean:
            return True
    return False

INCOME_KEYWORDS = [
    "penjualan", "jual", "omset", "omzet", "sales", "order", "gaji", "salary",
    "upah", "payroll", "masuk", "terima", "diterima", "penerimaan", "setor",
    "setoran", "modal", "piutang", "pelanggan", "customer", "tf masuk",
    "transfer masuk", "inflow", "pemasukan", "untung", "profit", "komisi",
    "bonus", "investasi", "dividen", "bunga bank", "bunga rekening", "cashback",
    "refund", "hibah", "donasi", "dp masuk", "pembayaran pelanggan",
    "invoice lunas", "pendapatan", "pelunasan piutang", "uang kas masuk"
]

EXPENSE_KEYWORDS = [
    "beli", "belanja", "biaya", "ongkos", "bayar", "pembayaran", "keluar",
    "pengeluaran", "makan", "minum", "bensin", "bbm", "pertalite", "pertamax",
    "listrik", "pln", "air", "pdam", "wifi", "pulsa", "sewa", "kontrak",
    "servis", "service", "maintenance", "gaji karyawan", "honor", "upah tukang",
    "staf", "iklan", "ads", "operasional", "atk", "transport", "parkir", "tol",
    "pajak", "retribusi", "supplier", "kulakan", "stok", "bahan", "uang keluar"
]

def is_income_description(desc: str) -> bool:
    desc_clean = desc.lower()
    return any(kw in desc_clean for kw in INCOME_KEYWORDS)

def is_expense_description(desc: str) -> bool:
    desc_clean = desc.lower()
    return any(kw in desc_clean for kw in EXPENSE_KEYWORDS)

def guess_category(description: str, txn_type: str) -> str:
    desc = description.lower()
    
    if txn_type == "INCOME":
        if any(w in desc for w in ["gaji", "salary", "upah", "payroll"]):
            return "Gaji & Upah"
        if any(w in desc for w in ["jual", "sales", "omset", "omzet", "order", "invoice", "pelanggan", "pembeli", "outlet", "toko", "barang"]):
            return "Penjualan & Omset"
        if any(w in desc for w in ["bunga", "bagi hasil", "dividen", "investasi"]):
            return "Investasi & Bunga"
        if any(w in desc for w in ["bonus", "komisi", "tips"]):
            return "Bonus & Komisi"
        if any(w in desc for w in ["piutang", "kembali", "refund", "kembalian"]):
            return "Pengembalian Dana"
        if any(w in desc for w in ["modal", "setoran"]):
            return "Setoran Modal"
        return "Pemasukan Lainnya"
    else:
        if any(w in desc for w in ["makan", "minum", "resto", "kopi", "cafe", "snack", "warung", "gofood", "grabfood", "shopeefood", "galon", "air"]):
            return "Makanan & Minuman"
        if any(w in desc for w in ["bensin", "bbm", "pertalite", "pertamax", "parkir", "tol", "ojol", "grab", "gojek", "transport", "ekspedisi"]):
            return "Transportasi & Bensin"
        if any(w in desc for w in ["listrik", "pln", "air pdam", "pdam", "internet", "wifi", "pulsa", "paket data", "token"]):
            return "Tagihan & Utilitas"
        if any(w in desc for w in ["gaji karyawan", "honor", "upah tukang", "staf", "karyawan"]):
            return "Gaji Karyawan"
        if any(w in desc for w in ["sewa", "rent", "kontrak", "gedung", "ruko"]):
            return "Sewa Tempat"
        if any(w in desc for w in ["bahan", "stok", "kulakan", "belanja barang", "supplier", "inventori"]):
            return "Belanja Stok & Bahan"
        if any(w in desc for w in ["iklan", "ads", "fb ads", "google ads", "tiktok", "promosi", "marketing"]):
            return "Pemasaran & Iklan"
        if any(w in desc for w in ["alat", "mesin", "perbaikan", "servis", "service", "maintenance", "ac"]):
            return "Pemeliharaan & Servis"
        return "Pengeluaran Operasional"

def clean_sheet_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df

    cols_str = " ".join([str(c).lower() for c in df.columns])
    has_header_keywords = any(k in cols_str for k in [
        "tgl", "tanggal", "date", "keterangan", "deskripsi", "nominal", "jumlah",
        "debit", "kredit", "masuk", "keluar", "pemasukan", "pengeluaran"
    ])
    
    if not has_header_keywords:
        header_idx = None
        for idx, row in df.head(10).iterrows():
            row_str = " ".join([str(val).lower() for val in row.values if pd.notna(val)])
            if any(k in row_str for k in [
                "tgl", "tanggal", "date", "keterangan", "deskripsi", "nominal", "jumlah",
                "debit", "kredit", "masuk", "keluar", "pemasukan", "pengeluaran"
            ]):
                header_idx = idx
                break
        if header_idx is not None:
            # Promote row to header
            new_header = df.iloc[header_idx]
            df = df.iloc[header_idx + 1:].copy()
            df.columns = new_header

    return df

def parse_single_dataframe(df: pd.DataFrame, default_sheet_type: Optional[str] = None, sheet_label: str = "") -> List[Dict[str, Any]]:
    if df.empty:
        return []

    date_col = None
    desc_col = None
    amount_col = None
    type_col = None
    income_col = None
    expense_col = None
    cat_col = None

    for col in df.columns:
        c = str(col).strip()
        # Date column
        if not date_col and match_col_keyword(c, ["tanggal", "tgl", "date", "waktu", "hari"]):
            date_col = col
        # Description column
        elif not desc_col and match_col_keyword(c, ["keterangan", "deskripsi", "uraian", "rincian", "perihal", "transaksi", "item", "memo", "description", "nama"]):
            desc_col = col
        # Income / Debit / Masuk column
        elif not income_col and match_col_keyword(c, ["pemasukan", "masuk", "inflow", "in", "uang masuk", "kas masuk", "debit", "debet", "penerimaan", "pendapatan", "kredit bank", "cr", "penjualan"]):
            income_col = col
        # Expense / Credit / Keluar column
        elif not expense_col and match_col_keyword(c, ["pengeluaran", "keluar", "outflow", "out", "uang keluar", "kas keluar", "kredit", "credit", "biaya", "beban", "debit bank", "dr", "penarikan"]):
            expense_col = col
        # Generic Amount column
        elif not amount_col and match_col_keyword(c, ["nominal", "jumlah", "total", "amount", "nilai", "rupiah", "saldo akhir"]):
            amount_col = col
        # Type indicator column
        elif not type_col and match_col_keyword(c, ["tipe", "jenis", "type", "arah", "arus", "d/k", "status", "mutasi"]):
            type_col = col
        # Category column
        elif not cat_col and match_col_keyword(c, ["kategori", "category", "pos", "golongan"]):
            cat_col = col

    # Fallback for description if not identified
    if not desc_col:
        for col in df.columns:
            if col not in [date_col, income_col, expense_col, amount_col, type_col, cat_col]:
                desc_col = col
                break

    parsed_txns = []

    for idx, row in df.iterrows():
        if row.isna().all():
            continue

        txn_date = parse_date_str(row[date_col]) if (date_col and pd.notna(row[date_col])) else datetime.now().strftime("%Y-%m-%d")
        txn_desc = str(row[desc_col]).strip() if (desc_col and pd.notna(row[desc_col])) else f"Transaksi Baris #{idx+1}"

        # CASE 1: Both Income and Expense columns exist
        if income_col and expense_col:
            val_in = clean_amount(row[income_col]) if pd.notna(row[income_col]) else 0.0
            val_out = clean_amount(row[expense_col]) if pd.notna(row[expense_col]) else 0.0

            if val_in > 0 and val_out == 0:
                parsed_txns.append({
                    "date": txn_date,
                    "description": txn_desc,
                    "type": "INCOME",
                    "amount": val_in,
                    "category": str(row[cat_col]).strip() if (cat_col and pd.notna(row[cat_col])) else guess_category(txn_desc, "INCOME"),
                    "note": f"{sheet_label} Baris {idx+1}".strip()
                })
            elif val_out > 0 and val_in == 0:
                parsed_txns.append({
                    "date": txn_date,
                    "description": txn_desc,
                    "type": "EXPENSE",
                    "amount": val_out,
                    "category": str(row[cat_col]).strip() if (cat_col and pd.notna(row[cat_col])) else guess_category(txn_desc, "EXPENSE"),
                    "note": f"{sheet_label} Baris {idx+1}".strip()
                })
            elif val_in > 0 and val_out > 0:
                # Both columns have values on same row: add both
                parsed_txns.append({
                    "date": txn_date,
                    "description": f"{txn_desc} (Pemasukan)",
                    "type": "INCOME",
                    "amount": val_in,
                    "category": guess_category(txn_desc, "INCOME"),
                    "note": f"{sheet_label} Baris {idx+1}".strip()
                })
                parsed_txns.append({
                    "date": txn_date,
                    "description": f"{txn_desc} (Pengeluaran)",
                    "type": "EXPENSE",
                    "amount": val_out,
                    "category": guess_category(txn_desc, "EXPENSE"),
                    "note": f"{sheet_label} Baris {idx+1}".strip()
                })
            continue

        # CASE 2: Only Income column exists
        if income_col and not expense_col:
            val_in = clean_amount(row[income_col]) if pd.notna(row[income_col]) else 0.0
            if val_in > 0:
                parsed_txns.append({
                    "date": txn_date,
                    "description": txn_desc,
                    "type": "INCOME",
                    "amount": val_in,
                    "category": str(row[cat_col]).strip() if (cat_col and pd.notna(row[cat_col])) else guess_category(txn_desc, "INCOME"),
                    "note": f"{sheet_label} Baris {idx+1}".strip()
                })
            continue

        # CASE 3: Only Expense column exists
        if expense_col and not income_col:
            val_out = clean_amount(row[expense_col]) if pd.notna(row[expense_col]) else 0.0
            if val_out > 0:
                parsed_txns.append({
                    "date": txn_date,
                    "description": txn_desc,
                    "type": "EXPENSE",
                    "amount": val_out,
                    "category": str(row[cat_col]).strip() if (cat_col and pd.notna(row[cat_col])) else guess_category(txn_desc, "EXPENSE"),
                    "note": f"{sheet_label} Baris {idx+1}".strip()
                })
            continue

        # CASE 4: Generic Amount column
        val_amt = clean_amount(row[amount_col]) if (amount_col and pd.notna(row[amount_col])) else 0.0

        if val_amt == 0:
            # Fallback scan for any numeric column
            for col in df.columns:
                if col not in [date_col, desc_col, cat_col, type_col]:
                    val_candidate = clean_amount(row[col])
                    if val_candidate != 0:
                        val_amt = val_candidate
                        break

        if val_amt == 0:
            continue

        # Determine type: INCOME vs EXPENSE
        txn_type = None

        # Check explicit type column
        if type_col and pd.notna(row[type_col]):
            t_str = str(row[type_col]).strip().lower()
            if any(x in t_str for x in ["masuk", "in", "pemasukan", "kredit", "cr", "income", "jual", "penjualan", "setor", "terima", "debet kas", "pendapatan"]):
                txn_type = "INCOME"
            elif any(x in t_str for x in ["keluar", "out", "pengeluaran", "debit", "dr", "expense", "biaya", "beban", "tarik", "bayar"]):
                txn_type = "EXPENSE"

        # Check sheet-level default if set
        if not txn_type and default_sheet_type:
            txn_type = default_sheet_type

        # Check description context
        if not txn_type:
            if is_income_description(txn_desc):
                txn_type = "INCOME"
            elif is_expense_description(txn_desc):
                txn_type = "EXPENSE"

        # Check negative sign (e.g. -50000 is expense, +50000 might be income)
        if not txn_type:
            if val_amt < 0:
                txn_type = "EXPENSE"
            else:
                # Positive amount: evaluate description keywords or default to INCOME if positive
                txn_type = "INCOME"

        cat_val = str(row[cat_col]).strip() if (cat_col and pd.notna(row[cat_col])) else guess_category(txn_desc, txn_type)

        parsed_txns.append({
            "date": txn_date,
            "description": txn_desc,
            "type": txn_type,
            "amount": abs(val_amt),
            "category": cat_val,
            "note": f"{sheet_label} Baris {idx+1}".strip()
        })

    return parsed_txns

def parse_excel_file(file_path: str) -> Dict[str, Any]:
    """
    Parses an Excel (.xlsx, .xls) or CSV file and extracts structured transactions.
    Supports multiple sheets, distinct Income/Expense columns, and smart type classification.
    """
    all_transactions = []
    detected_cols = {}

    try:
        if file_path.lower().endswith(".csv"):
            try:
                df = pd.read_csv(file_path, sep=None, engine="python")
            except Exception:
                try:
                    df = pd.read_csv(file_path, sep=";")
                except Exception:
                    df = pd.read_csv(file_path, sep=",")
            df = clean_sheet_dataframe(df)
            txns = parse_single_dataframe(df)
            all_transactions.extend(txns)
        else:
            # Excel: read all sheets
            excel_sheets = pd.read_excel(file_path, sheet_name=None)
            for sheet_name, df_sheet in excel_sheets.items():
                if df_sheet.empty:
                    continue

                # Check sheet name hints
                s_lower = str(sheet_name).lower()
                default_type = None
                if any(k in s_lower for k in ["masuk", "pemasukan", "income", "penjualan", "omset", "penerimaan"]):
                    default_type = "INCOME"
                elif any(k in s_lower for k in ["keluar", "pengeluaran", "expense", "biaya", "beban"]):
                    default_type = "EXPENSE"

                cleaned_df = clean_sheet_dataframe(df_sheet)
                sheet_label = f"[{sheet_name}]" if len(excel_sheets) > 1 else ""
                sheet_txns = parse_single_dataframe(cleaned_df, default_sheet_type=default_type, sheet_label=sheet_label)
                all_transactions.extend(sheet_txns)
    except Exception as e:
        return {"success": False, "error": f"Gagal membaca berkas: {str(e)}", "transactions": []}

    if not all_transactions:
        return {"success": False, "error": "Tidak ada data transaksi yang dapat dibaca dari berkas ini.", "transactions": []}

    # Assign 1-indexed temp_id and calculate income vs expense counts
    income_count = sum(1 for t in all_transactions if t["type"] == "INCOME")
    expense_count = sum(1 for t in all_transactions if t["type"] == "EXPENSE")

    for idx, t in enumerate(all_transactions):
        t["temp_id"] = idx + 1

    return {
        "success": True,
        "total_parsed": len(all_transactions),
        "income_count": income_count,
        "expense_count": expense_count,
        "transactions": all_transactions
    }
