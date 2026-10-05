import time

from app.core.config import get_settings
from app.tests.conftest import make_image


def _wait(client, auth, job_id, timeout=15):
    deadline = time.time() + timeout
    while time.time() < deadline:
        j = client.get(f"/api/v1/jobs/{job_id}", headers=auth).json()
        if j["status"] in ("completed", "failed"):
            return j
        time.sleep(0.05)
    raise AssertionError("job did not finish")


def test_thumbnail_follows_clean_image_in_public_catalog(client, auth, catalog):
    r = client.post(
        "/api/v1/products/upload",
        data={"catalog_id": catalog["id"]},
        files={"file": ("f.jpg", make_image(), "image/jpeg")},
        headers=auth,
    )
    pid = r.json()["id"]
    job = client.get("/api/v1/jobs", headers=auth, params={"product_id": pid}).json()[0]
    _wait(client, auth, job["id"])
    client.patch(
        f"/api/v1/products/{pid}",
        json={"name": "X", "price": 1, "status": "published"},
        headers=auth,
    )
    client.post(f"/api/v1/catalogs/{catalog['id']}/publish", headers=auth)
    p = client.get(f"/api/v1/public/catalogs/{catalog['slug']}").json()["products"][0]
    assert p["image"].endswith("clean.jpg")  # mock returns original bytes (jpeg)
    assert p["image_small"].endswith("thumbnail.jpg")
    # switching to original invalidates the derived thumbnail → falls back to full image
    client.patch(f"/api/v1/products/{pid}", json={"primary_asset_type": "original"}, headers=auth)
    p = client.get(f"/api/v1/public/catalogs/{catalog['slug']}").json()["products"][0]
    assert p["image"].endswith("original.jpg") and p["image_small"] == p["image"]


def test_brand_models_crud_and_usage(client, auth, brand, catalog, monkeypatch):
    r = client.post(
        f"/api/v1/brands/{brand['id']}/models",
        json={
            "name": "Modelo principal",
            "gender": "mujer",
            "age_range": "25-35",
            "style": "editorial",
            "prompt_template": "Foto {style} de modelo {gender}",
        },
        headers=auth,
    )
    assert r.status_code == 201
    bm = r.json()
    assert (
        client.get(f"/api/v1/brands/{brand['id']}/models", headers=auth).json()[0]["id"] == bm["id"]
    )

    monkeypatch.setattr(get_settings(), "virtual_model_enabled", True)
    r = client.post(
        "/api/v1/products/upload",
        data={"catalog_id": catalog["id"], "auto_process": "false"},
        files={"file": ("f.jpg", make_image(), "image/jpeg")},
        headers=auth,
    )
    pid = r.json()["id"]
    r = client.post(
        f"/api/v1/products/{pid}/generate-model", json={"brand_model_id": bm["id"]}, headers=auth
    )
    assert r.status_code == 202
    job = _wait(client, auth, r.json()["id"])
    assert (
        job["status"] == "completed"
        and job["result"]["options"]["model"]["name"] == "Modelo principal"
    )
    assert job["result"]["options"]["style"] == "editorial"

    r = client.post(
        f"/api/v1/products/{pid}/generate-model", json={"brand_model_id": "nope"}, headers=auth
    )
    assert r.status_code == 404
    assert (
        client.delete(f"/api/v1/brands/{brand['id']}/models/{bm['id']}", headers=auth).status_code
        == 204
    )
    assert client.get(f"/api/v1/brands/{brand['id']}/models", headers=auth).json() == []


def test_experiments_compare_providers(client, auth, catalog):
    from app.tests.test_admin import _make_admin

    _make_admin("juan@example.com")
    r = client.post(
        "/api/v1/admin/ai/experiments",
        json={
            "task": "product_name",
            "providers": ["local", "mock", "ninerouter"],
            "payload": {"attributes": {"category": "camiseta", "color": "ivory"}},
        },
        headers=auth,
    )
    assert r.status_code == 200
    res = {x["provider"]: x for x in r.json()["results"]}
    assert res["local"]["success"] and res["local"]["data"]["name"] == "Camiseta Ivory"
    assert res["mock"]["success"] and "Essential" in res["mock"]["data"]["name"]
    assert res["ninerouter"]["success"] is False

    r = client.post(
        "/api/v1/products/upload",
        data={"catalog_id": catalog["id"], "auto_process": "false"},
        files={"file": ("f.jpg", make_image(), "image/jpeg")},
        headers=auth,
    )
    pid = r.json()["id"]
    r = client.post(
        "/api/v1/admin/ai/experiments",
        json={"task": "product_recognition", "providers": ["local", "mock"], "product_id": pid},
        headers=auth,
    )
    out = r.json()["results"]
    assert all(x["success"] for x in out) and out[0]["data"]["color"] == "ivory"
    assert (
        client.post(
            "/api/v1/admin/ai/experiments",
            json={"task": "nope", "providers": ["mock"]},
            headers=auth,
        ).status_code
        == 422
    )
