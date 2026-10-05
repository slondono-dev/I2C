import time

from app.tests.conftest import make_image


def _wait_job(client, auth, job_id, timeout=10):
    deadline = time.time() + timeout
    while time.time() < deadline:
        job = client.get(f"/api/v1/jobs/{job_id}", headers=auth).json()
        if job["status"] in ("completed", "failed"):
            return job
        time.sleep(0.05)
    raise AssertionError("job did not finish")


def test_upload_creates_product_and_runs_pipeline(client, auth, catalog, image_bytes):
    r = client.post(
        "/api/v1/products/upload",
        data={"catalog_id": catalog["id"]},
        files={"file": ("foto.jpg", image_bytes, "image/jpeg")},
        headers=auth,
    )
    assert r.status_code == 201, r.text
    product = r.json()
    types = {a["type"] for a in product["assets"]}
    assert "original" in types and "thumbnail" in types

    jobs = client.get("/api/v1/jobs", headers=auth, params={"product_id": product["id"]}).json()
    assert len(jobs) == 1
    job = _wait_job(client, auth, jobs[0]["id"])
    assert job["status"] == "completed", job
    assert job["result"]["analyze"]["recognition"]["success"] is True
    assert job["result"]["clean"]["success"] is True

    p = client.get(f"/api/v1/products/{product['id']}", headers=auth).json()
    assert p["status"] == "review"
    assert p["name"]
    assert p["description"]
    assert p["color"]
    assert "clean" in {a["type"] for a in p["assets"]}
    assert p["ai_metadata"]["recognition"]["provider"]


def test_upload_rejects_invalid_files(client, auth, catalog):
    r = client.post(
        "/api/v1/products/upload",
        data={"catalog_id": catalog["id"]},
        files={"file": ("x.jpg", b"not an image", "image/jpeg")},
        headers=auth,
    )
    assert r.status_code == 422
    tiny = make_image(size=(10, 10))
    r = client.post(
        "/api/v1/products/upload",
        data={"catalog_id": catalog["id"]},
        files={"file": ("x.jpg", tiny, "image/jpeg")},
        headers=auth,
    )
    assert r.status_code == 422


def test_publish_requires_name_price_image(client, auth, catalog, image_bytes):
    r = client.post(
        "/api/v1/products", json={"catalog_id": catalog["id"], "name": "Sin foto"}, headers=auth
    )
    pid = r.json()["id"]
    r = client.patch(
        f"/api/v1/products/{pid}", json={"status": "published", "price": 10}, headers=auth
    )
    assert r.status_code == 422

    r = client.post(
        "/api/v1/products/upload",
        data={"catalog_id": catalog["id"], "auto_process": "false"},
        files={"file": ("foto.jpg", image_bytes, "image/jpeg")},
        headers=auth,
    )
    pid2 = r.json()["id"]
    r = client.patch(f"/api/v1/products/{pid2}", json={"status": "published"}, headers=auth)
    assert r.status_code == 422  # no name/price

    r = client.patch(
        f"/api/v1/products/{pid2}",
        json={
            "status": "published",
            "name": "Camiseta",
            "price": 79900,
            "stock": 5,
            "variants": [{"size": "S", "stock": 2}, {"size": "M", "stock": 3}],
        },
        headers=auth,
    )
    assert r.status_code == 200 and r.json()["status"] == "published"
    assert len(r.json()["variants"]) == 2

    r = client.post(
        "/api/v1/products/bulk/publish", json={"product_ids": [pid, pid2]}, headers=auth
    )
    assert r.json()["published"] == [pid2]
    assert r.json()["errors"][0]["id"] == pid


def test_public_catalog_and_whatsapp(client, auth, brand, catalog, image_bytes):
    assert client.get(f"/api/v1/public/catalogs/{catalog['slug']}").status_code == 404
    client.post(f"/api/v1/catalogs/{catalog['id']}/publish", headers=auth)

    r = client.post(
        "/api/v1/products/upload",
        data={"catalog_id": catalog["id"], "auto_process": "false"},
        files={"file": ("foto.jpg", image_bytes, "image/jpeg")},
        headers=auth,
    )
    pid = r.json()["id"]
    client.patch(
        f"/api/v1/products/{pid}",
        json={
            "status": "published",
            "name": "Camiseta Essential Ivory",
            "price": 79900,
            "sku": "CAM-001",
            "stock": 3,
        },
        headers=auth,
    )
    # draft products must not appear
    client.post(
        "/api/v1/products", json={"catalog_id": catalog["id"], "name": "Borrador"}, headers=auth
    )

    r = client.get(f"/api/v1/public/catalogs/{catalog['slug']}")
    assert r.status_code == 200
    data = r.json()
    assert data["brand"]["name"] == "Mi Marca"
    assert len(data["products"]) == 1
    p = data["products"][0]
    assert p["available"] is True
    assert p["image"]
    assert p["whatsapp_url"].startswith("https://wa.me/573001234567?text=")
    assert "CAM-001" in p["whatsapp_url"]
    assert "79.900" in p["whatsapp_url"]

    qr = client.get(f"/api/v1/public/catalogs/{catalog['slug']}/qr.png")
    assert qr.status_code == 200 and qr.headers["content-type"] == "image/png"


def test_bulk_update_and_filters(client, auth, catalog):
    ids = [
        client.post(
            "/api/v1/products",
            json={"catalog_id": catalog["id"], "name": f"P{i}", "category": "camiseta"},
            headers=auth,
        ).json()["id"]
        for i in range(3)
    ]
    r = client.post(
        "/api/v1/products/bulk/update",
        json={"items": [{"id": ids[0], "price": 1000, "stock": 2}, {"id": ids[1], "stock": 20}]},
        headers=auth,
    )
    assert r.status_code == 200
    low = client.get("/api/v1/products", headers=auth, params={"low_stock": 5}).json()
    assert [p["id"] for p in low] == [ids[0]]
    cat = client.get("/api/v1/products", headers=auth, params={"category": "camiseta"}).json()
    assert len(cat) == 3

    assert client.delete(f"/api/v1/products/{ids[2]}", headers=auth).status_code == 204
    assert client.get(f"/api/v1/products/{ids[2]}", headers=auth).status_code == 404
