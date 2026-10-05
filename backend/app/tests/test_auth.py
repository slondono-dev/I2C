def test_register_login_me(client):
    r = client.post(
        "/api/v1/auth/register", json={"name": "A", "email": "a@x.com", "password": "secret1"}
    )
    assert r.status_code == 201
    token = r.json()["access_token"]

    r = client.post(
        "/api/v1/auth/register", json={"name": "A", "email": "a@x.com", "password": "secret1"}
    )
    assert r.status_code == 409

    r = client.post("/api/v1/auth/login", json={"email": "a@x.com", "password": "wrong"})
    assert r.status_code == 401

    r = client.post("/api/v1/auth/login", json={"email": "A@X.com", "password": "secret1"})
    assert r.status_code == 200

    r = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200 and r.json()["email"] == "a@x.com"

    assert client.get("/api/v1/auth/me").status_code == 401
    assert (
        client.get("/api/v1/auth/me", headers={"Authorization": "Bearer nope"}).status_code == 401
    )
