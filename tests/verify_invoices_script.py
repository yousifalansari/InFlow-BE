from fastapi.testclient import TestClient
from main import app
import random
import string
import datetime

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
        "company_name": "TestCorp"
    })
    
    login_res = client.post("/api/login", json={
        "username": username,
        "password": password
    })
    token = login_res.json()["token"]
    return {"Authorization": f"Bearer {token}"}

def test_invoices_flow():
    headers = get_auth_headers()

    # 1. Create Client
    client_res = client.post("/api/clients/", json={
        "name": "Invoice Client",
        "email": f"invoice-{random_string()}@example.com"
    }, headers=headers)
    assert client_res.status_code == 201
    client_id = client_res.json()["id"]

    # 2. Create Quote
    quote_res = client.post("/api/quotes/", json={
        "client_id": client_id,
        "expiry_date": str(datetime.date.today() + datetime.timedelta(days=7)),
        "line_items": [
            {"description": "Project X", "quantity": 1, "rate": 1000.0}
        ]
    }, headers=headers)
    assert quote_res.status_code == 201
    quote = quote_res.json()
    quote_id = quote["id"]
    # Total = 1000 + 100 tax = 1100

    # 3. Create Invoice from Quote
    invoice_data = {
        "quote_id": quote_id,
        "due_date": str(datetime.date.today() + datetime.timedelta(days=30)),
        "status": "sent"
    }
    invoice_res = client.post("/api/invoices/", json=invoice_data, headers=headers)
    assert invoice_res.status_code == 201, invoice_res.text
    invoice = invoice_res.json()
    print("Invoice created:", invoice)
    
    assert invoice["total"] == 1100.0
    assert invoice["balance_due"] == 1100.0
    invoice_id = invoice["id"]

    # 4. Get Invoice PDF
    pdf_res = client.get(f"/api/invoices/{invoice_id}/pdf", headers=headers)
    assert pdf_res.status_code == 200
    assert pdf_res.headers["content-type"] == "application/pdf"
    assert len(pdf_res.content) > 0
    print("Invoice PDF verified")
    
    # 5. Check duplicate Invoice creation (should fail)
    dup_res = client.post("/api/invoices/", json=invoice_data, headers=headers)
    assert dup_res.status_code == 400

if __name__ == "__main__":
    test_invoices_flow()
