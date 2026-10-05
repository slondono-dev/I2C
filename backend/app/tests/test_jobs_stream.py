import json
import time

from app.tests.conftest import make_image


def _upload(client, auth, catalog, auto="false"):
    r = client.post(
        "/api/v1/products/upload",
        data={"catalog_id": catalog["id"], "auto_process": auto},
        files={"file": ("f.jpg", make_image(), "image/jpeg")},
        headers=auth,
    )
    assert r.status_code == 201
    return r.json()


def test_bulk_reprocess_and_sse_stream(client, auth, catalog):
    ids = [_upload(client, auth, catalog)["id"] for _ in range(2)]
    r = client.post(
        "/api/v1/products/bulk/reprocess",
        json={"product_ids": ids + ["missing"], "task": "analyze"},
        headers=auth,
    )
    assert r.status_code == 202 and len(r.json()) == 2
    job_id = r.json()[0]["id"]

    with client.stream("GET", f"/api/v1/jobs/{job_id}/stream", headers=auth) as resp:
        assert resp.status_code == 200
        assert resp.headers["content-type"].startswith("text/event-stream")
        events = []
        for line in resp.iter_lines():
            if line.startswith("data: "):
                events.append(json.loads(line[6:]))
    assert events[-1] == {}  # end event
    statuses = [e["status"] for e in events[:-1]]
    assert statuses[-1] == "completed"

    deadline = time.time() + 10
    while time.time() < deadline:
        p = client.get(f"/api/v1/products/{ids[1]}", headers=auth).json()
        if p["status"] == "review":
            break
        time.sleep(0.05)
    assert p["name"]

    # idempotent: a second reprocess while pending/running reuses the job (none active now → new)
    r = client.post(
        "/api/v1/products/bulk/reprocess", json={"product_ids": ids, "task": "clean"}, headers=auth
    )
    assert r.status_code == 202 and len(r.json()) == 2


def test_stream_requires_ownership(client, auth, catalog):
    p = _upload(client, auth, catalog, auto="true")
    job = client.get("/api/v1/jobs", headers=auth, params={"product_id": p["id"]}).json()[0]
    r = client.post(
        "/api/v1/auth/register", json={"name": "B", "email": "b@x.com", "password": "secret1"}
    )
    other = {"Authorization": f"Bearer {r.json()['access_token']}"}
    assert client.get(f"/api/v1/jobs/{job['id']}/stream", headers=other).status_code == 404
