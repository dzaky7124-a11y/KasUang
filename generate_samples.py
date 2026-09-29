import os
from pathlib import Path
import pandas as pd

sample_dir = Path("sample_data")
sample_dir.mkdir(parents=True, exist_ok=True)

# Sample 1: Kas Usaha / UMKM with Tanggal, Keterangan, Masuk, Keluar, Saldo, Kategori
data_umkm = [
    {"Tanggal": "2024-03-01", "Keterangan": "Saldo Awal Kas Usaha", "Masuk": 5000000, "Keluar": 0, "Kategori": "Pemasukan Lainnya"},
    {"Tanggal": "2024-03-02", "Keterangan": "Penjualan Produk Batch 1", "Masuk": 2450000, "Keluar": 0, "Kategori": "Penjualan & Omset"},
    {"Tanggal": "2024-03-03", "Keterangan": "Belanja Bahan Baku dan Kemasan", "Masuk": 0, "Keluar": 1200000, "Kategori": "Belanja Stok & Bahan"},
    {"Tanggal": "2024-03-04", "Keterangan": "Beli Token Listrik Toko", "Masuk": 0, "Keluar": 250000, "Kategori": "Tagihan & Utilitas"},
    {"Tanggal": "2024-03-05", "Keterangan": "Penjualan Tokopedia & Shopee", "Masuk": 3800000, "Keluar": 0, "Kategori": "Penjualan & Omset"},
    {"Tanggal": "2024-03-06", "Keterangan": "Biaya Iklan Instagram & TikTok Ads", "Masuk": 0, "Keluar": 500000, "Kategori": "Pemasaran & Iklan"},
    {"Tanggal": "2024-03-07", "Keterangan": "Makan Siang & Konsumsi Tim Kerja", "Masuk": 0, "Keluar": 185000, "Kategori": "Makanan & Minuman"},
    {"Tanggal": "2024-03-08", "Keterangan": "Bensin & Operasional Kirim Barang", "Masuk": 0, "Keluar": 120000, "Kategori": "Transportasi & Bensin"},
    {"Tanggal": "2024-03-09", "Keterangan": "Penjualan Catering Kantor", "Masuk": 4200000, "Keluar": 0, "Kategori": "Penjualan & Omset"},
    {"Tanggal": "2024-03-10", "Keterangan": "Servis Printer & Perlengkapan Nota", "Masuk": 0, "Keluar": 350000, "Kategori": "Pemeliharaan & Servis"},
]

df_excel = pd.DataFrame(data_umkm)
df_excel.to_excel(sample_dir / "contoh_kas_masuk_keluar.xlsx", index=False)
print("Excel sample created:", sample_dir / "contoh_kas_masuk_keluar.xlsx")

# Sample 2: CSV format with semicolon delimiter
data_csv = [
    {"Tgl": "15/03/2024", "Deskripsi": "Omset Harian Outlet 1", "Nominal": 1750000, "Tipe": "Masuk"},
    {"Tgl": "16/03/2024", "Deskripsi": "Beli Galon Air & Kebutuhan Kantor", "Nominal": 85000, "Tipe": "Keluar"},
    {"Tgl": "17/03/2024", "Deskripsi": "Service AC Ruang Kasir", "Nominal": 200000, "Tipe": "Keluar"},
    {"Tgl": "18/03/2024", "Deskripsi": "Pesanan Grosir Bpk Budi", "Nominal": 5200000, "Tipe": "Masuk"},
    {"Tgl": "19/03/2024", "Deskripsi": "Biaya Parkir & Tol Ekspedisi", "Nominal": 65000, "Tipe": "Keluar"},
]
df_csv = pd.DataFrame(data_csv)
df_csv.to_csv(sample_dir / "contoh_kas_umkm.csv", sep=";", index=False)
print("CSV sample created:", sample_dir / "contoh_kas_umkm.csv")
