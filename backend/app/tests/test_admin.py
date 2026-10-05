from app.core.db import SessionLocal
from app.models import User


def _make_admin(email):
    db = SessionLocal()
    u = db.query(User).filter_by(email=email).one()
    u.is_admin = True
    db.commit()
    db.close()


def test_admin_endpoints_require_admin(client, auth):
    assert client.get("/api/v1/admin/ai/providers", headers=auth).status_code == 403
    _make_admin("juan@example.com")
    r = client.get("/api/v1/admin/ai/providers", headers=auth)
    assert r.status_code == 200
    names = {p["name"] for p in r.json()}
    assert {"mock", "local", "ninerouter", "openrouter", "anthropic"} <= names
    nine = next(p for p in r.json() if p["name"] == "ninerouter")
    assert nine["status"] == "disabled" and nine["configured"] is False

    r = client.patch(
        "/api/v1/admin/ai/providers/local", json={"enabled": False, "priority": 5}, headers=auth
    )
    assert r.status_code == 200
    local = next(p for p in r.json() if p["name"] == "local")
    assert local["enabled"] is False and local["priority"] == 5

    r = client.get("/api/v1/admin/ai/routing", headers=auth)
    assert r.status_code == 200
    rec = next(t for t in r.json() if t["task"] == "product_recognition")
    assert rec["active"] == "mock"  # local disabled → mock

    r = client.get("/api/v1/admin/ai/usage", headers=auth)
    assert r.status_code == 200 and "free_ratio" in r.json()
    assert client.get("/api/v1/admin/ai/features", headers=auth).json()["ninerouter"] is False
    # restore
    client.patch("/api/v1/admin/ai/providers/local", json={"enabled": True}, headers=auth)


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200 and r.json()["status"] == "ok"


def test_health_check_endpoint(client, auth):
    _make_admin("juan@example.com")
    r = client.post("/api/v1/admin/ai/health-check", headers=auth)
    assert r.status_code == 200
    data = r.json()
    assert data["mock"] is True and data["local"] is True
    assert data["ninerouter"] is False  # disabled → not configured
