from fastapi.testclient import TestClient
from main import app
import random
import string
import datetime
import csv
import io

client = TestClient(app)

def random_string(length=10):
    return ''.join(random.choices(string.ascii_lowercase, k=length))

def get_auth_headers():
    username = random_string()
    email = f"{username}@example.com"
    password = "password123"
    
    register_res = client.post("/api/register", json={
        "username": username,
        "email": email,
        "password": password,
        "company_name": "InFlow Inc"
    })
    
    login_res = client.post("/api/login", json={
        "username": username,
        "password": password
    })
    token = login_res.json()["token"]
    return {"Authorization": f"Bearer {token}"}

def test_payments_analytics_flow():
    headers = get_auth_headers()

    # 1. Setup: Create Client, Quote, Invoice
    client_res = client.post("/api/clients/", json={
        "name": "Big Corp",
        "email": f"bigcorp-{random_string()}@example.com"
    }, headers=headers)
    client_id = client_res.json()["id"]

    quote_res = client.post("/api/quotes/", json={
        "client_id": client_id,
        "line_items": [{"description": "Dev Work", "quantity": 10, "rate": 100.0}]
    }, headers=headers)
    quote_id = quote_res.json()["id"]
    # Total = 1000 + 100 tax = 1100

    invoice_res = client.post("/api/invoices/", json={
        "quote_id": quote_id,
        "due_date": str(datetime.date.today() + datetime.timedelta(days=30))
    }, headers=headers)
    invoice = invoice_res.json()
    invoice_id = invoice["id"]
    print(f"Invoice {invoice['invoice_number']} created with balance: {invoice['balance_due']}")

    # 2. Make Partial Payment
    payment1_data = {
        "amount": 500.0,
        "method": "bank_transfer",
        "reference": "TXN_001"
    }
    payment1_res = client.post(f"/api/invoices/{invoice_id}/payments", json=payment1_data, headers=headers)
    assert payment1_res.status_code == 201
    print("Partial payment of 500 made")

    # Verify Invoice Balance Updated (Need to refetch invoice)
    invoice_updated = client.get(f"/api/invoices/{invoice_id}", headers=headers).json()
    assert invoice_updated["balance_due"] == 600.0 # 1100 - 500
    assert invoice_updated["status"] == "sent" # Still sent/partial

    # 3. Make Remaining Payment
    payment2_data = {
        "amount": 600.0,
        "method": "stripe",
        "reference": "TXN_002"
    }
    payment2_res = client.post(f"/api/invoices/{invoice_id}/payments", json=payment2_data, headers=headers)
    assert payment2_res.status_code == 201
    print("Remaining payment of 600 made")

    invoice_final = client.get(f"/api/invoices/{invoice_id}", headers=headers).json()
    assert invoice_final["balance_due"] == 0.0
    assert invoice_final["status"] == "paid"
    print("Invoice fully paid")

    # 4. Verify Analytics Summary
    summary_res = client.get("/api/analytics/summary", headers=headers)
    assert summary_res.status_code == 200
    summary = summary_res.json()
    print("Analytics Summary:", summary)
    
    assert summary["total_revenue_this_month"] == 1100.0
    assert summary["total_outstanding"] == 0.0 # No other invoices
    assert len(summary["revenue_by_client"]) >= 1
    assert summary["revenue_by_client"][0]["total"] == 1100.0

    # 5. Verify CSV Export
    csv_res = client.get("/api/analytics/export", headers=headers)
    assert csv_res.status_code == 200
    assert "text/csv" in csv_res.headers["content-type"]
    
    content = csv_res.text
    print("CSV Content Head:")
    print("\n".join(content.splitlines()[:5]))
    assert "Big Corp,1100.0" in content

if __name__ == "__main__":
    test_payments_analytics_flow()
