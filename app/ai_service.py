import json
import logging
from typing import Dict, Any, List, Optional
from google import genai
from google.genai import types
from sqlmodel import Session, select
from app.config import GEMINI_API_KEY as ENV_GEMINI_KEY, GEMINI_MODEL
from app.models import SystemConfig

logger = logging.getLogger("kaspintar.ai")

def get_effective_gemini_key(session: Optional[Session] = None) -> str:
    """Retrieve Gemini key from database config or environment variable."""
    if session:
        try:
            config_entry = session.exec(select(SystemConfig).where(SystemConfig.key == "GEMINI_API_KEY")).first()
            if config_entry and config_entry.value.strip():
                return config_entry.value.strip()
        except Exception as e:
            logger.warning(f"Error fetching DB GEMINI_API_KEY: {e}")
    return ENV_GEMINI_KEY.strip() if ENV_GEMINI_KEY else ""

def get_gemini_client(api_key: Optional[str] = None, session: Optional[Session] = None):
    key = api_key or get_effective_gemini_key(session)
    if not key:
        return None
    return genai.Client(api_key=key)

def parse_excel_with_gemini(raw_rows_text: str, api_key: Optional[str] = None, session: Optional[Session] = None) -> Dict[str, Any]:
    """
    Uses Gemini AI to parse unstructured or complex Excel rows into structured transactions.
    """
    client = get_gemini_client(api_key, session)
    if not client:
        return {
            "success": False,
            "error": "Google Gemini API Key belum diatur. Silakan atur API Key di menu Pengaturan Admin atau gunakan parser otomatis bawaan."
        }

    prompt = f"""
Anda adalah asisten AI akuntansi profesional Indonesia.
Tugas Anda adalah membaca data baris tabel excel kas/keuangan mentah berikut dan mengekstrak SEMUA transaksi keuangan (BAIK PEMASUKAN MAUPUN PENGELUARAN) menjadi JSON array yang rapi.

PERHATIAN UTAMA:
- JANGAN HANYA MENGAMBIL PENGELUARAN!
- Anda WAJIB mengekstrak KEDUA JENIS TRANSAKSI:
  1. PEMASUKAN ("type": "INCOME"): Semua uang masuk, penjualan produk/jasa, omset, gaji masuk, setoran modal, pembayaran piutang, bunga bank, transfer masuk, saldo awal.
  2. PENGELUARAN ("type": "EXPENSE"): Semua uang keluar, belanja stok, pembelian bahan, biaya operasional, makan/minum, bensin, listrik, sewa, gaji staf, promosi/iklan, perbaikan.

Data Tabel Mentah:
\"\"\"
{raw_rows_text}
\"\"\"

Pedoman Penentuan Kolom & Tipe:
- Jika ada kolom 'Masuk' / 'Pemasukan' / 'Debit Kas' / 'Penerimaan' / 'Kredit Bank': baris dengan nominal di kolom ini bernilai "type": "INCOME".
- Jika ada kolom 'Keluar' / 'Pengeluaran' / 'Kredit Kas' / 'Biaya' / 'Debit Bank': baris dengan nominal di kolom ini bernilai "type": "EXPENSE".
- Jika hanya ada satu kolom nominal dan kolom tipe/keterangan:
  * "Masuk", "Pemasukan", "Penjualan", "Omset", "Setoran", "Terima", "CR" -> "INCOME"
  * "Keluar", "Pengeluaran", "Biaya", "Bayar", "Beli", "Beban", "DR" -> "EXPENSE"

Struktur JSON yang WAJIB dikembalikan:
{{
  "transactions": [
    {{
      "date": "2024-03-01",
      "description": "Penjualan Toko",
      "type": "INCOME",
      "amount": 2500000,
      "category": "Penjualan & Omset",
      "note": ""
    }},
    {{
      "date": "2024-03-02",
      "description": "Beli Bahan Baku",
      "type": "EXPENSE",
      "amount": 750000,
      "category": "Belanja Stok & Bahan",
      "note": ""
    }}
  ]
}}
"""
    try:
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.1,
                response_mime_type="application/json"
            )
        )
        text = response.text.strip()
        data = json.loads(text)
        txns = data.get("transactions", [])
        
        income_count = sum(1 for t in txns if t.get("type", "").upper() == "INCOME")
        expense_count = sum(1 for t in txns if t.get("type", "").upper() == "EXPENSE")

        # Assign temp_id
        for idx, t in enumerate(txns):
            t["temp_id"] = idx + 1
            t["type"] = t.get("type", "INCOME").upper()
            if t["type"] not in ["INCOME", "EXPENSE"]:
                t["type"] = "INCOME" if any(w in t.get("description", "").lower() for w in ["jual", "omset", "masuk", "gaji"]) else "EXPENSE"

        return {
            "success": True,
            "total_parsed": len(txns),
            "income_count": income_count,
            "expense_count": expense_count,
            "transactions": txns,
            "mode": "gemini_ai"
        }
    except Exception as e:
        logger.error(f"Gemini Excel parse error: {e}")
        return {
            "success": False,
            "error": f"Gagal memproses dengan Gemini AI: {str(e)}"
        }

def analyze_financial_health_with_gemini(
    summary_data: Dict[str, Any],
    recent_transactions: List[Dict[str, Any]],
    api_key: Optional[str] = None,
    session: Optional[Session] = None
) -> Dict[str, Any]:
    """
    Evaluates financial health, spending patterns, anomalies, recommendations, and forecast.
    Falls back to robust algorithmic analysis if no Gemini key is provided.
    """
    client = get_gemini_client(api_key, session)
    
    # Calculate rule-based baseline statistics
    total_income = summary_data.get("total_income", 0.0)
    total_expense = summary_data.get("total_expense", 0.0)
    current_balance = summary_data.get("current_balance", 0.0)
    net_savings = total_income - total_expense
    savings_rate = (net_savings / total_income * 100) if total_income > 0 else 0.0

    # Rule-based health score calculation
    if total_income == 0 and total_expense == 0:
        base_score = 75
        base_status = "Baru Memulai"
    elif net_savings >= 0:
        if savings_rate >= 30:
            base_score = 90
            base_status = "Sangat Sehat"
        elif savings_rate >= 15:
            base_score = 80
            base_status = "Sehat"
        else:
            base_score = 65
            base_status = "Cukup Sehat (Margin Tipis)"
    else:
        burn_ratio = abs(net_savings) / (total_expense or 1)
        if burn_ratio > 0.5:
            base_score = 35
            base_status = "Kritis (Defisit Parah)"
        else:
            base_score = 50
            base_status = "Waspada (Pengeluaran Melebihi Pemasukan)"

    # If no AI client available, return high-quality rule-based insights
    if not client:
        top_categories = summary_data.get("expense_by_category", {})
        top_cat_name = list(top_categories.keys())[0] if top_categories else "Umum"
        top_cat_amount = list(top_categories.values())[0] if top_categories else 0.0

        recommendations = [
            f"Perhatikan kategori '{top_cat_name}' yang menjadi pos pengeluaran terbesar (Rp {top_cat_amount:,.0f}). Pertimbangkan evaluasi efisiensi pada pos ini.",
            "Terapkan alokasi anggaran 50/30/20 (50% kebutuhan operasional, 30% pengembangan, 20% dana darurat/cadangan kas).",
            "Jaga rasio pemasukan tetap lebih tinggi dari pengeluaran dengan target tabungan/laba kas minimal 20% per bulan.",
            "Hubungkan Google Gemini API Key di menu Pengaturan Admin untuk mengaktifkan analisis AI otomatis mendalam & interaktif."
        ]

        anomalies = []
        if total_expense > total_income and total_income > 0:
            anomalies.append(f"Arus kas saat ini negatif (-Rp {abs(net_savings):,.0f}). Pengeluaran melampaui pemasukan sebesar {abs(savings_rate):.1f}%.")
        if savings_rate > 50:
            anomalies.append(f"Kondisi kas surplus sangat tinggi ({savings_rate:.1f}% tabungan). Anda memiliki ruang investasi kas atau ekspansi bisnis yang baik.")

        return {
            "score": base_score,
            "status": base_status,
            "savings_rate_pct": round(savings_rate, 1),
            "summary_text": f"Kondisi kas Anda berstatus '{base_status}' dengan total pemasukan Rp {total_income:,.0f} dan total pengeluaran Rp {total_expense:,.0f} (Net: Rp {net_savings:,.0f}).",
            "recommendations": recommendations,
            "anomalies": anomalies,
            "forecast_next_month": {
                "estimated_cashflow": net_savings,
                "projected_balance": current_balance + net_savings,
                "confidence": "Berdasarkan rata-rata histori periode aktif"
            },
            "source": "algorithmic_baseline"
        }

    # If Gemini client IS available, ask Gemini for an executive financial diagnosis
    prompt = f"""
Anda adalah Chief Financial Officer (CFO) & Penasihat Keuangan AI berpengalaman tinggi.
Analisis data kas keuangan pengguna berikut:

RINGKASAN KEUANGAN:
- Total Pemasukan: Rp {total_income:,.0f}
- Total Pengeluaran: Rp {total_expense:,.0f}
- Saldo Kas Saat Ini: Rp {current_balance:,.0f}
- Selisih Bersih (Cashflow): Rp {net_savings:,.0f}
- Rasio Tabungan/Surplus: {savings_rate:.1f}%
- Pengeluaran per Kategori: {json.dumps(summary_data.get('expense_by_category', {}), ensure_ascii=False)}
- Pemasukan per Kategori: {json.dumps(summary_data.get('income_by_category', {}), ensure_ascii=False)}
- Sampel Transaksi Terkini: {json.dumps(recent_transactions[:15], ensure_ascii=False)}

TUGAS ANDA:
Berikan analisis mendalam, tajam, mudah dipahami dalam Bahasa Indonesia, dan kembalikan HANYA format JSON valid dengan struktur:
{{
  "score": (integer 1-100 skor kesehatan keuangan),
  "status": "(Sangat Sehat / Sehat / Waspada / Kritis)",
  "summary_text": "(Ringkasan eksekutif 2-3 kalimat mengenai kondisi kas saat ini)",
  "recommendations": [
    "(Rekomendasi taktis 1 yang spesifik berdasarkan kategori pengeluaran terbesar)",
    "(Rekomendasi taktis 2 terkait efisiensi biaya / kenaikan pendapatan)",
    "(Rekomendasi taktis 3 strategi pengelolaan cadangan kas)"
  ],
  "anomalies": [
    "(Peringatan deteksi pos pengeluaran yang boros/bengkak atau risiko likuiditas jika ada)"
  ],
  "forecast_next_month": {{
    "estimated_cashflow": (proyeksi selisih kas bulan depan dalam float),
    "projected_balance": (proyeksi estimasi saldo kas akhir bulan depan dalam float),
    "advice": "(Nasihat singkat untuk proyeksi bulan depan)"
  }}
}}
"""
    try:
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.3,
                response_mime_type="application/json"
            )
        )
        res_data = json.loads(response.text.strip())
        res_data["savings_rate_pct"] = round(savings_rate, 1)
        res_data["source"] = "gemini_ai"
        return res_data
    except Exception as e:
        logger.error(f"Gemini Financial analysis error: {e}")
        # Fallback to algorithmic if API call fails
        return {
            "score": base_score,
            "status": base_status,
            "savings_rate_pct": round(savings_rate, 1),
            "summary_text": f"Kondisi kas Anda berstatus '{base_status}' dengan arus kas bersih Rp {net_savings:,.0f}.",
            "recommendations": [
                "Periksa pengeluaran harian dan catat secara rutin.",
                "Prioritaskan pengeluaran primer operasional.",
                "Pertahankan dana cadangan kas minimal 3 bulan pengeluaran rutin."
            ],
            "anomalies": [],
            "forecast_next_month": {
                "estimated_cashflow": net_savings,
                "projected_balance": current_balance + net_savings,
                "advice": "Tingkatkan kontrol pengeluaran untuk menjaga surplus."
            },
            "source": f"algorithmic_fallback (Error AI: {str(e)})"
        }

def chat_with_financial_ai(
    user_message: str,
    chat_history: List[Dict[str, str]],
    financial_context: Dict[str, Any],
    api_key: Optional[str] = None,
    session: Optional[Session] = None
) -> str:
    """
    Interactive AI assistant for user queries regarding their financial records.
    """
    client = get_gemini_client(api_key, session)
    if not client:
        return (
            "Fitur percakapan interaktif AI memerlukan Google Gemini API Key. "
            "Silakan minta Administrator untuk memasukkan Google Gemini API Key pada menu Pengaturan Admin, "
            "atau Anda dapat melihat ringkasan analisis keuangan otomatis pada kartu di atas."
        )

    system_instruction = f"""
Anda adalah KasPintar AI, asisten dan konsultan keuangan pribadi & UMKM yang ramah, cerdas, profesional, dan selalu memberikan saran yang praktis dalam Bahasa Indonesia.
Anda memiliki akses ke data buku kas pengguna saat ini:

DATA KEUANGAN PENGGUNA:
- Saldo Kas Saat Ini: Rp {financial_context.get('current_balance', 0):,.0f}
- Total Pemasukan: Rp {financial_context.get('total_income', 0):,.0f}
- Total Pengeluaran: Rp {financial_context.get('total_expense', 0):,.0f}
- Arus Kas Bersih: Rp {financial_context.get('net_cashflow', 0):,.0f}
- Daftar Akun Kas / Dompet: {json.dumps(financial_context.get('wallets', []), ensure_ascii=False)}
- Rincian Pengeluaran per Kategori: {json.dumps(financial_context.get('expense_by_category', {}), ensure_ascii=False)}
- Rincian Pemasukan per Kategori: {json.dumps(financial_context.get('income_by_category', {}), ensure_ascii=False)}

Pedoman Respon:
1. Jawab pertanyaan pengguna secara akurat berdasarkan angka data riil di atas.
2. Berikan saran taktis, tips penghematan, atau ide peningkatan arus kas yang aplikatif.
3. Gunakan format Markdown yang menarik (gunakan poin-poin, bold untuk angka penting).
4. Tetap ramah, suportif, dan solutif.
"""

    contents = []
    # Add recent history (up to last 6 messages)
    for msg in chat_history[-6:]:
        role = "user" if msg.get("role") == "user" else "model"
        contents.append(types.Content(
            role=role,
            parts=[types.Part.from_text(text=msg.get("content", ""))]
        ))
    
    # Add current user message
    contents.append(types.Content(
        role="user",
        parts=[types.Part.from_text(text=user_message)]
    ))

    try:
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=0.4
            )
        )
        return response.text.strip()
    except Exception as e:
        logger.error(f"Gemini Chat error: {e}")
        return f"Mohon maaf, terjadi kendala saat menghubungi AI: {str(e)}"
