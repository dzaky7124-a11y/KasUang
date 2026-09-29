# KasPintar AI 💼🤖
**Aplikasi Pembukuan Kas, Pengeluaran & Pemasukan Multiplatform (Web & Android) dengan Cloud dan Kecerdasan Buatan (Google Gemini AI)**

---

## 🌟 Fitur Utama

1. **Multiplatform (Web & Android PWA Modern)**:
   - **Web Desktop**: Tampilan dashboard lengkap dengan grafik interaktif Chart.js, filter transaksi, ekspor data, dan panel admin.
   - **Android**: Responsif mobile-first dengan navigasi bawah (bottom navigation), floating action button, dan dukungan **Progressive Web App (PWA)** sehingga bisa di-install langsung ke layar utama Android layaknya aplikasi native tanpa perlu Google Play Store.

2. **Manajemen Kas & Arus Keuangan (Cashflow Management)**:
   - Pencatatan Pemasukan, Pengeluaran, dan Transfer Antar Kas.
   - Multi-Akun Kas: Kas Tunai, Rekening Bank (BCA, Mandiri, dll.), Dompet Digital (GoPay, OVO, Dana).
   - Pengelompokan Kategori Otomatis & Kategori Kustom.
   - Filter lengkap berdasarkan rentang tanggal, kategori, akun kas, tipe, dan pencarian teks.
   - Ekspor laporan pembukuan ke **Excel (.xlsx)** dan **CSV**.

3. **Panel Admin & Manajemen Akun (Role-Based Access Control / RBAC)**:
   - **Akun Pertama** yang mendaftar otomatis menjadi **ADMIN**.
   - Admin dapat melihat semua pengguna terdaftar dan statistik global sistem.
   - Admin dapat menambah user baru, membekukan/mengaktifkan akun, mengubah peran (Admin/User), dan mereset kata sandi.

4. **Siap Cloud (Cloud-Ready & Anti-Hilang)**:
   - **Pencadangan Cloud 1-Klik**: Unduh seluruh rekaman database ke berkas cadangan JSON aman kapan saja.
   - **Pemulihan Data (Restore)**: Unggah berkas cadangan JSON untuk memulihkan seluruh data kas dan transaksi.
   - Kompatibel dengan database cloud seperti **PostgreSQL / Supabase / Neon / Railway** cukup dengan mengisi `DATABASE_URL` di file `.env`.

5. **AI Pembaca Berkas Excel Cerdas (Smart Excel Reader & Importer)**:
   - Pengguna tidak perlu memasukkan transaksi satu per satu jika sudah memiliki catatan di Excel atau CSV.
   - **Pendeteksi Otomatis Cerdas (Offline)**: Otomatis membaca kolom tanggal, keterangan, debit/kredit, nominal, dan menebak kategori tanpa perlu internet atau API key.
   - **Mode AI Deep Scan (Google Gemini)**: Membaca tabel kas yang tidak beraturan / catatan bebas menjadi data transaksi terstruktur.
   - **Tabel Pratinjau Interaktif**: Cek dan pilih transaksi yang ingin diimpor sebelum disimpan ke akun kas.

6. **AI Analisis Finansial & Konsultan Keuangan Cerdas**:
   - **Skor Kesehatan Keuangan (0-100)**: Evaluasi likuiditas dan rasio tabungan kas.
   - **Rekomendasi Taktis AI**: Saran konkret penghematan dan efisiensi biaya.
   - **Deteksi Anomali**: Peringatan otomatis pos pengeluaran yang melonjak tajam atau berisiko defisit.
   - **Proyeksi Arus Kas**: Estimasi saldo dan cashflow bulan berikutnya.
   - **Chat Interaktif Asisten Keuangan**: Konsultasi tanya-jawab langsung seputar kondisi kas Anda dalam Bahasa Indonesia.

---

## 🚀 Cara Menjalankan Aplikasi

Aplikasi telah disiapkan menggunakan virtual environment Python lokal:

### 1. Menjalankan Server
Buka terminal PowerShell di folder proyek ini dan jalankan:

```powershell
.\.venv\Scripts\python.exe run.py
```

Server akan aktif pada:
- **Akses dari Komputer (Web)**: `http://localhost:8000`
- **Akses dari HP Android**: `http://<IP-Laptop-Anda>:8000` *(IP akan ditampilkan otomatis di terminal saat server berjalan)*.

---

## 📱 Cara Memasang di HP Android (PWA)

1. Pastikan HP Android Anda terhubung ke **jaringan Wi-Fi yang sama** dengan komputer/laptop Anda.
2. Buka browser **Google Chrome** di HP Android Anda.
3. Ketik alamat IP yang muncul di terminal (contoh: `http://192.168.1.10:8000`).
4. Ketuk tombol banner **"Pasang Sekarang"** yang muncul di bagian atas aplikasi, atau:
   - Ketuk menu titik tiga (⋮) di pojok kanan atas Chrome.
   - Pilih **"Tambahkan ke Layar Utama"** (*Add to Home Screen*) / **"Install App"**.
5. Ikon **KasPintar AI** akan muncul di layar utama Android dan dapat dibuka fullscreen layaknya aplikasi aplikasi Android biasa!

---

## 🔑 Konfigurasi Google Gemini API Key

Fitur AI bawaan sudah dilengkapi dengan parser offline cerdas. Untuk mengaktifkan kemampuan analisis AI mendalam dari Google Gemini:

1. Buka aplikasi dan masuk sebagai **Admin**.
2. Masuk ke menu **Panel Admin** di bilah navigasi.
3. Pada kartu **Konfigurasi Google Gemini AI**, masukkan API Key Anda (dapat diperoleh gratis di [Google AI Studio](https://aistudio.google.com)).
4. Klik **Simpan API Key**. Seluruh pengguna di sistem kini dapat menggunakan analisis Gemini AI dan fitur chat asisten!

---

## 📁 Struktur Berkas Proyek

```
Project APPS/
│
├── app/
│   ├── config.py           # Konfigurasi aplikasi & database
│   ├── database.py         # Inisialisasi engine SQLModel & session
│   ├── models.py           # Model data (User, Wallet, Category, Transaction, SystemConfig)
│   ├── auth.py             # Keamanan JWT & otorisasi peran (RBAC)
│   ├── ai_service.py       # Integrasi Google Gemini AI (Excel parser & Financial Analyst)
│   ├── excel_parser.py     # Parser cerdas Excel (.xlsx, .xls) & CSV
│   ├── routers/
│   │   ├── auth.py         # Login, Register, Profil
│   │   ├── wallets.py      # Kelola Akun Kas & Saldo
│   │   ├── categories.py   # Kelola Kategori
│   │   ├── transactions.py # Catat, Filter, Ekspor Transaksi
│   │   ├── excel_import.py # Upload & Pratinjau Excel
│   │   ├── ai_analytics.py # Diagnostik Keuangan & Chat AI
│   │   └── admin.py        # Panel Admin, Pengguna & Backup Cloud
│   └── main.py             # Server FastAPI & Static Files
│
├── static/
│   ├── css/custom.css      # Styling custom & safe area mobile
│   ├── js/
│   │   ├── api.js          # Client API & format mata uang Rupiah
│   │   ├── auth.js         # Pengelolaan sesi & hak akses
│   │   ├── charts.js       # Grafik visual interaktif Chart.js
│   │   └── app.js          # Logika frontend utama SPA
│   ├── manifest.json       # Web App Manifest PWA Android
│   ├── sw.js               # Service Worker untuk caching
│   ├── icons/              # Ikon aplikasi Android & Web (192px, 512px)
│   └── index.html          # Halaman utama aplikasi responsif
│
├── sample_data/
│   ├── contoh_kas_masuk_keluar.xlsx # Sampel data Excel untuk uji coba
│   └── contoh_kas_umkm.csv          # Sampel data CSV untuk uji coba
│
├── run.py                  # Skrip startup 1-klik
├── generate_samples.py     # Generator berkas uji coba
├── generate_icons.py       # Generator ikon PWA
└── README.md
```
