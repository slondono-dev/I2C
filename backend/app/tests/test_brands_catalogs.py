def test_brand_creates_default_catalog_and_unique_slugs(client, auth):
    r1 = client.post("/api/v1/brands", json={"name": "Marca Uno"}, headers=auth)
    r2 = client.post("/api/v1/brands", json={"name": "Marca Uno"}, headers=auth)
    assert r1.status_code == 201 and r2.status_code == 201
    assert r1.json()["slug"] == "marca-uno"
    assert r2.json()["slug"] == "marca-uno-2"

    cats = client.get("/api/v1/catalogs", headers=auth).json()
    assert len(cats) == 2
    assert {c["slug"] for c in cats} == {"marca-uno", "marca-uno-2"}
    assert cats[0]["public_url"].endswith("/c/marca-uno")


def test_catalog_publish_and_qr(client, auth, catalog):
    r = client.post(f"/api/v1/catalogs/{catalog['id']}/publish", headers=auth)
    assert r.status_code == 200 and r.json()["status"] == "published"
    assert r.json()["published_at"] is not None

    qr = client.get(f"/api/v1/catalogs/{catalog['id']}/qr.png", headers=auth)
    assert qr.status_code == 200 and qr.headers["content-type"] == "image/png"
    assert qr.content[:8] == b"\x89PNG\r\n\x1a\n"


def test_authorization_between_users(client, auth, brand):
    r = client.post(
        "/api/v1/auth/register", json={"name": "B", "email": "b@x.com", "password": "secret1"}
    )
    other = {"Authorization": f"Bearer {r.json()['access_token']}"}
    assert client.get(f"/api/v1/brands/{brand['id']}", headers=other).status_code == 404
    assert client.get("/api/v1/brands", headers=other).json() == []
