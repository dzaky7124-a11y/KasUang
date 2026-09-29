import uvicorn
import socket
import sys

# Ensure UTF-8 output on Windows console
try:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('10.254.254.254', 1))
        ip = s.getsockname()[0]
    except Exception:
        ip = '127.0.0.1'
    finally:
        s.close()
    return ip

if __name__ == "__main__":
    local_ip = get_local_ip()
    port = 8000

    print("=" * 65)
    print(" [KASPINTAR AI] - APLIKASI KAS & KEUANGAN CLOUD MULTIPLATFORM")
    print("=" * 65)
    print(f" Akses dari Komputer (Web) : http://localhost:{port}")
    print(f" Akses dari HP Android     : http://{local_ip}:{port}")
    print("=" * 65)
    print(" Petunjuk Pemasangan di Android:")
    print(f" 1. Sambungkan HP Android ke Wi-Fi yang sama dengan PC.")
    print(f" 2. Buka Chrome di HP dan kunjungi: http://{local_ip}:{port}")
    print(" 3. Ketuk banner 'Pasang Sekarang' atau menu titik tiga Chrome")
    print("    lalu pilih 'Tambahkan ke Layar Utama' / 'Install App'.")
    print("=" * 65)

    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=True)
