from google import genai
from app.database import get_session
from app.models import SystemConfig
from sqlmodel import select
import json

session = next(get_session())
k = session.exec(select(SystemConfig).where(SystemConfig.key=='GEMINI_API_KEY')).first().value
client = genai.Client(api_key=k)

test_csv = """Tanggal,Keterangan,Pemasukan,Pengeluaran
2024-04-01,Penjualan Minuman Boba,250000,0
2024-04-02,Beli Es Batu dan Cup,0,45000
2024-04-03,Terima Transfer Pelanggan,500000,0
2024-04-04,Bayar Listrik Stand,0,80000
"""

prompt = f"""Anda adalah akuntan profesional. Ekstrak data tabel berikut menjadi JSON array transaksi kas (BAIK PEMASUKAN MAUPUN PENGELUARAN).
Wajib tentukan:
- 'date': YYYY-MM-DD
- 'description': keterangan
- 'type': 'INCOME' untuk pemasukan, 'EXPENSE' untuk pengeluaran
- 'amount': nominal angka positif
- 'category': kategori dalam bahasa Indonesia

Data:
{test_csv}

Format JSON:
{{"transactions": [{{"date": "2024-04-01", "description": "Penjualan", "type": "INCOME", "amount": 250000, "category": "Penjualan"}}]}}
"""

res = client.models.generate_content(
    model='gemini-3.8-flash',
    contents=prompt,
    config={'response_mime_type': 'application/json'}
)
print("GEMINI OUTPUT:")
data = json.loads(res.text)
for t in data["transactions"]:
    print(f"[{t['type']}] {t['description']} - Rp {t['amount']:,} ({t['category']})")
