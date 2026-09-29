import requests
import json
import time

BASE_URL = "http://127.0.0.1:8000"

def test_api():
    print("Testing server connectivity...")
    # 1. Health / Index
    r = requests.get(BASE_URL + "/")
    assert r.status_code == 200, f"Index failed: {r.status_code}"
    print("[OK] Index HTML OK!")

    # 2. PWA Manifest & SW
    r_man = requests.get(BASE_URL + "/manifest.json")
    assert r_man.status_code == 200, "Manifest failed"
    print("[OK] PWA Manifest OK!")

    r_sw = requests.get(BASE_URL + "/sw.js")
    assert r_sw.status_code == 200, "Service worker failed"
    print("[OK] Service Worker OK!")

    # 3. Register First User (Admin)
    reg_data = {
        "name": "Budi Admin",
        "email": "admin@kaspintar.id",
        "password": "password123"
    }
    r_reg = requests.post(BASE_URL + "/api/auth/register", json=reg_data)
    if r_reg.status_code == 200:
        res = r_reg.json()
        print("[OK] Registered Admin:", res["user"]["name"], "- Role:", res["user"]["role"])
        token = res["access_token"]
    else:
        # Try login if already registered
        r_log = requests.post(BASE_URL + "/api/auth/login", json={"email": "admin@kaspintar.id", "password": "password123"})
        assert r_log.status_code == 200, f"Login failed: {r_log.text}"
        res = r_log.json()
        print("[OK] Logged In:", res["user"]["name"], "- Role:", res["user"]["role"])
        token = res["access_token"]

    headers = {"Authorization": f"Bearer {token}"}

    # 4. Check Wallets
    r_wallets = requests.get(BASE_URL + "/api/wallets", headers=headers)
    assert r_wallets.status_code == 200, "Wallets list failed"
    wallets = r_wallets.json()["wallets"]
    print(f"[OK] User Wallets ({len(wallets)} found):", [w["name"] for w in wallets])
    main_wallet_id = wallets[0]["id"]

    # 5. Check Categories
    r_cats = requests.get(BASE_URL + "/api/categories", headers=headers)
    assert r_cats.status_code == 200, "Categories list failed"
    cats = r_cats.json()["categories"]
    print(f"[OK] Categories loaded: {len(cats)} categories")

    # 6. Test Excel Parse Upload
    with open("sample_data/contoh_kas_masuk_keluar.xlsx", "rb") as f:
        r_parse = requests.post(
            BASE_URL + "/api/excel/parse",
            files={"file": ("contoh_kas_masuk_keluar.xlsx", f, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
            data={"use_ai": "false"},
            headers=headers
        )
    assert r_parse.status_code == 200, f"Parse failed: {r_parse.text}"
    parse_data = r_parse.json()
    print(f"[OK] Excel Parse Success: {parse_data['total_parsed']} transactions detected!")

    # 7. Test Bulk Import of Parsed Transactions
    txns_to_import = [
        {
            "date": t["date"],
            "description": t["description"],
            "type": t["type"],
            "amount": t["amount"],
            "category_name": t["category"],
            "note": t["note"]
        }
        for t in parse_data["transactions"]
    ]
    r_import = requests.post(
        BASE_URL + "/api/excel/confirm-import",
        json={"wallet_id": main_wallet_id, "transactions": txns_to_import},
        headers=headers
    )
    assert r_import.status_code == 200, f"Import failed: {r_import.text}"
    print("[OK] Confirm Bulk Import:", r_import.json()["message"])

    # 8. Check Transactions & Summary
    r_txns = requests.get(BASE_URL + "/api/transactions", headers=headers)
    assert r_txns.status_code == 200
    print(f"[OK] Transactions List: {r_txns.json()['total']} transactions in database")

    r_summary = requests.get(BASE_URL + "/api/transactions/summary", headers=headers)
    assert r_summary.status_code == 200
    s = r_summary.json()
    print(f"[OK] Summary: Income Rp {s['total_income']:,.0f} | Expense Rp {s['total_expense']:,.0f} | Net Rp {s['net_cashflow']:,.0f}")

    # 9. Test AI Health Check Endpoint
    r_ai = requests.get(BASE_URL + "/api/ai/health-check", headers=headers)
    assert r_ai.status_code == 200
    ai_res = r_ai.json()
    print("[OK] AI Health Check Score:", ai_res["analysis"]["score"], "-", ai_res["analysis"]["status"])
    print("     AI Summary:", ai_res["analysis"]["summary_text"])

    # 10. Check Admin System Stats
    r_stats = requests.get(BASE_URL + "/api/admin/system-stats", headers=headers)
    assert r_stats.status_code == 200
    st = r_stats.json()
    print(f"[OK] Admin Stats: Users: {st['total_users']}, Transactions: {st['total_transactions']}, Total Volume: Rp {st['total_volume']:,.0f}")

    print("\nSUCCESS: ALL 10 TESTS PASSED! The application is 100% operational.")

if __name__ == "__main__":
    time.sleep(1)
    test_api()
