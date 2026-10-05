import time

from app.core.config import get_settings
from app.services.images.fidelity import fidelity_score, needs_review
from app.tests.conftest import make_image


def _wait(client, auth, job_id, timeout=15):
    deadline = time.time() + timeout
    while time.time() < deadline:
        j = client.get(f"/api/v1/jobs/{job_id}", headers=auth).json()
        if j["status"] in ("completed", "failed"):
            return j
        time.sleep(0.05)
    raise AssertionError("job did not finish")


def _upload(client, auth, catalog, color=(30, 60, 160)):
    r = client.post(
        "/api/v1/products/upload",
        data={"catalog_id": catalog["id"], "auto_process": "false"},
        files={"file": ("f.jpg", make_image(color), "image/jpeg")},
        headers=auth,
    )
    assert r.status_code == 201
    return r.json()


def test_generate_model_and_video_disabled_by_default(client, auth, catalog):
    p = _upload(client, auth, catalog)
    assert (
        client.post(f"/api/v1/products/{p['id']}/generate-model", headers=auth).status_code == 503
    )
    assert (
        client.post(f"/api/v1/products/{p['id']}/generate-video", headers=auth).status_code == 503
    )


def test_generate_model_and_video_with_mock(client, auth, catalog, monkeypatch):
    s = get_settings()
    monkeypatch.setattr(s, "virtual_model_enabled", True)
    monkeypatch.setattr(s, "video_enabled", True)
    p = _upload(client, auth, catalog)

    r = client.post(
        f"/api/v1/products/{p['id']}/generate-model",
        json={"style": "editorial", "model": {"gender": "female"}},
        headers=auth,
    )
    assert r.status_code == 202
    job = _wait(client, auth, r.json()["id"])
    assert job["status"] == "completed", job
    assert job["result"]["model"]["success"] is True, job["result"]
    assert 0 <= job["result"]["model"]["fidelity_score"] <= 1

    r = client.post(f"/api/v1/products/{p['id']}/generate-video", headers=auth)
    assert r.status_code == 202
    job = _wait(client, auth, r.json()["id"])
    assert job["status"] == "completed", job

    prod = client.get(f"/api/v1/products/{p['id']}", headers=auth).json()
    types = {a["type"] for a in prod["assets"]}
    assert {"original", "model", "video"} <= types
    assert prod["ai_metadata"]["virtual_model"]["fidelity_score"] >= 0

    # catalog can show the model image and exposes the video
    client.patch(
        f"/api/v1/products/{p['id']}",
        json={"name": "X", "price": 10, "status": "published", "primary_asset_type": "model"},
        headers=auth,
    )
    client.post(f"/api/v1/catalogs/{catalog['id']}/publish", headers=auth)
    pub = client.get(f"/api/v1/public/catalogs/{catalog['slug']}").json()
    assert pub["products"][0]["image"].endswith("model.jpg")
    assert pub["products"][0]["video"].endswith("video.gif")
    assert pub["products"][0]["images"]["model"]


def test_fidelity_score_flags_colour_drift():
    blue, blue2, red = (
        make_image((30, 60, 160)),
        make_image((35, 65, 165)),
        make_image((200, 30, 40)),
    )
    same = fidelity_score(blue, blue2)
    diff = fidelity_score(blue, red)
    assert same > diff
    assert not needs_review(same)
    assert needs_review(diff)


def test_brand_logo_upload(client, auth, brand):
    r = client.post(
        f"/api/v1/brands/{brand['id']}/logo",
        files={"file": ("logo.png", make_image((10, 10, 10), (300, 300), "PNG"), "image/png")},
        headers=auth,
    )
    assert r.status_code == 200 and r.json()["logo"].endswith("logo.png")
    r = client.post(
        f"/api/v1/brands/{brand['id']}/logo",
        files={"file": ("logo.png", b"nope", "image/png")},
        headers=auth,
    )
    assert r.status_code == 422


def test_metrics_endpoint(client, auth, catalog):
    from app.tests.test_admin import _make_admin

    _make_admin("juan@example.com")
    r = client.post(
        "/api/v1/products/upload",
        data={"catalog_id": catalog["id"]},
        files={"file": ("f.jpg", make_image(), "image/jpeg")},
        headers=auth,
    )
    pid = r.json()["id"]
    job = client.get("/api/v1/jobs", headers=auth, params={"product_id": pid}).json()[0]
    _wait(client, auth, job["id"])
    client.patch(f"/api/v1/products/{pid}", json={"price": 5, "status": "published"}, headers=auth)
    m = client.get("/api/v1/admin/ai/metrics", headers=auth).json()
    assert m["products_processed"] == 1
    assert m["products_published"] == 1
    assert m["photo_to_product_seconds_avg"] is not None
    assert m["product_to_catalog_seconds_avg"] is not None
    assert m["ai_cost_per_product"] == 0.0
    assert m["free_provider_ratio"] == 1.0
