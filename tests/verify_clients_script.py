from fastapi.testclient import TestClient
from main import app
import random
import string

client = TestClient(app)

def random_string(length=10):
    return ''.join(random.choices(string.ascii_lowercase, k=length))

def test_clients_flow():
    # 1. Register a new user
    username = random_string()
    email = f"{username}@example.com"
    password = "password123"
    
    register_res = client.post("/api/register", json={
        "username": username,
        "email": email,
        "password": password,
        "company_name": "TestCorp"
    })
    assert register_res.status_code == 200, register_res.text
    
    # 2. Login
    login_res = client.post("/api/login", json={
        "username": username,
        "password": password
    })
    assert login_res.status_code == 200, login_res.text
    token = login_res.json()["token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 3. Create Client
    client_data = {
        "name": "Acme Inc",
        "email": f"contact-{random_string()}@acme.com",
        "phone": "555-0123",
        "address": "123 Main St"
    }
    create_res = client.post("/api/clients/", json=client_data, headers=headers)
    assert create_res.status_code == 201, create_res.text
    created_client = create_res.json()
    assert created_client["name"] == client_data["name"]
    assert created_client["user_id"] is not None
    client_id = created_client["id"]
    print("Client created:", created_client)

    # 4. List Clients
    list_res = client.get("/api/clients/", headers=headers)
    assert list_res.status_code == 200
    clients = list_res.json()
    assert len(clients) >= 1
    assert any(c["id"] == client_id for c in clients)
    print("Client list verified")

    # 5. Get Client Detail
    get_res = client.get(f"/api/clients/{client_id}", headers=headers)
    assert get_res.status_code == 200
    assert get_res.json()["id"] == client_id

    # 6. Update Client
    update_data = {"name": "Acme Corp (Updated)"}
    update_res = client.put(f"/api/clients/{client_id}", json=update_data, headers=headers)
    assert update_res.status_code == 200
    updated_client = update_res.json()
    assert updated_client["name"] == "Acme Corp (Updated)"
    print("Client updated:", updated_client)

    # 7. Delete Client
    del_res = client.delete(f"/api/clients/{client_id}", headers=headers)
    assert del_res.status_code == 204
    
    # Verify deletion
    get_res_after = client.get(f"/api/clients/{client_id}", headers=headers)
    assert get_res_after.status_code == 404
    print("Client deleted verified")

if __name__ == "__main__":
    test_clients_flow()
