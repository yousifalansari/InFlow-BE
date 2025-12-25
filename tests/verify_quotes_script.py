from fastapi.testclient import TestClient
from main import app
import random
import string
import datetime

client = TestClient(app)

def random_string(length=10):
    return ''.join(random.choices(string.ascii_lowercase, k=length))

def get_auth_headers():
    # Helper to get auth headers with a new user
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

def test_quotes_flow():
    headers = get_auth_headers()

    # 1. Create a Client
    client_data = {
        "name": "Quote Client",
        "email": f"quote-{random_string()}@example.com"
    }
    client_res = client.post("/api/clients/", json=client_data, headers=headers)
    assert client_res.status_code == 201
    client_id = client_res.json()["id"]

    # 2. Create a Quote with Line Items
    quote_data = {
        "client_id": client_id,
        "expiry_date": str(datetime.date.today() + datetime.timedelta(days=7)),
        "line_items": [
            {"description": "Service A", "quantity": 10, "rate": 50.0},
            {"description": "Product B", "quantity": 2, "rate": 100.0}
        ]
    }
    # Expected: (10*50) + (2*100) = 500 + 200 = 700 subtotal. 
    # Tax 10% = 70. Total = 770.
    
    create_res = client.post("/api/quotes/", json=quote_data, headers=headers)
    assert create_res.status_code == 201, create_res.text
    quote = create_res.json()
    print("Quote created:", quote)
    
    assert quote["subtotal"] == 700.0
    assert quote["tax"] == 70.0
    assert quote["total"] == 770.0
    assert len(quote["line_items"]) == 2
    quote_id = quote["id"]

    # 3. Get Quote PDF
    pdf_res = client.get(f"/api/quotes/{quote_id}/pdf", headers=headers)
    assert pdf_res.status_code == 200
    assert pdf_res.headers["content-type"] == "application/pdf"
    assert len(pdf_res.content) > 0
    print("PDF generation verified")

    # 4. Update Quote
    update_data = {
        "status": "sent",
        "line_items": [
            {"description": "Service A", "quantity": 5, "rate": 50.0} # Reduced quantity
        ]
    }
    # Expected: 5*50 = 250 subtotal. Tax 25. Total 275.
    
    update_res = client.put(f"/api/quotes/{quote_id}", json=update_data, headers=headers)
    assert update_res.status_code == 200, update_res.text
    updated_quote = update_res.json()
    print("Quote updated:", updated_quote)
    
    assert updated_quote["subtotal"] == 250.0
    assert updated_quote["total"] == 275.0
    assert updated_quote["status"] == "sent"
    assert len(updated_quote["line_items"]) == 1

if __name__ == "__main__":
    test_quotes_flow()
