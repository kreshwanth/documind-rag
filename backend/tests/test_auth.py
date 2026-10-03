def test_register_user_success(client):
    payload = {
        "name": "Sarah Connor",
        "email": "sarah@cyberdyne.com",
        "password": "securepassword123"
    }
    response = client.post("/api/auth/register", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == "sarah@cyberdyne.com"
    assert data["user"]["name"] == "Sarah Connor"

def test_register_duplicate_email_fails(client, test_user):
    payload = {
        "name": "Duplicate User",
        "email": test_user.email,
        "password": "anotherpassword"
    }
    response = client.post("/api/auth/register", json=payload)
    assert response.status_code == 400
    assert "already exists" in response.json()["detail"]

def test_login_success(client, test_user):
    response = client.post(
        "/api/auth/login",
        json={"email": test_user.email, "password": "password123"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["user"]["email"] == test_user.email

def test_login_invalid_password(client, test_user):
    response = client.post(
        "/api/auth/login",
        json={"email": test_user.email, "password": "wrongpassword"}
    )
    assert response.status_code == 401
    assert "Incorrect email or password" in response.json()["detail"]

def test_read_me_authenticated(client, auth_headers_user1, test_user):
    response = client.get("/api/auth/me", headers=auth_headers_user1)
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == test_user.email
    assert data["id"] == str(test_user.id)

def test_read_me_unauthorized(client):
    response = client.get("/api/auth/me")
    assert response.status_code == 401
