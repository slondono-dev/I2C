from __future__ import annotations

import os
import tempfile
from io import BytesIO

import pytest
from fastapi.testclient import TestClient
from PIL import Image

_tmp = tempfile.mkdtemp(prefix="i2c-test-")
os.environ.update(
    {
        "APP_MODE": "test",
        "DATABASE_URL": f"sqlite:///{_tmp}/test.db",
        "MEDIA_ROOT": f"{_tmp}/media",
        "SECRET_KEY": "test-secret",
        "MOCK_PROVIDERS_ENABLED": "true",
        "ANTHROPIC_API_KEY": "",
        "OPENROUTER_API_KEY": "",
        "LOCAL_REMBG_ENABLED": "false",
    }
)

from app.core.db import Base, engine  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture(autouse=True)
def _fresh_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture
def auth(client):
    r = client.post(
        "/api/v1/auth/register",
        json={"name": "Juan", "email": "juan@example.com", "password": "secret123"},
    )
    assert r.status_code == 201, r.text
    token = r.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def brand(client, auth):
    r = client.post(
        "/api/v1/brands", json={"name": "Mi Marca", "whatsapp": "+57 300 1234567"}, headers=auth
    )
    assert r.status_code == 201, r.text
    return r.json()


@pytest.fixture
def catalog(client, auth, brand):
    r = client.get("/api/v1/catalogs", headers=auth, params={"brand_id": brand["id"]})
    assert r.status_code == 200
    return r.json()[0]


def make_image(color=(250, 245, 230), size=(400, 400), fmt="JPEG") -> bytes:
    buf = BytesIO()
    Image.new("RGB", size, color).save(buf, format=fmt)
    return buf.getvalue()


@pytest.fixture
def image_bytes():
    return make_image()
