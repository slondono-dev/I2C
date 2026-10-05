from __future__ import annotations

from functools import lru_cache

from app.core.config import get_settings
from app.services.storage.base import StorageProvider
from app.services.storage.local import LocalStorageProvider


@lru_cache
def get_storage() -> StorageProvider:
    s = get_settings()
    if s.storage_provider == "s3":
        from app.services.storage.s3 import S3CompatibleProvider

        return S3CompatibleProvider(
            s.s3_bucket, s.s3_endpoint_url, s.s3_access_key, s.s3_secret_key, s.s3_region
        )
    base = s.media_url if s.media_url.startswith("http") else f"{s.api_base_url}{s.media_url}"
    return LocalStorageProvider(s.media_root, base)


__all__ = ["StorageProvider", "get_storage"]
