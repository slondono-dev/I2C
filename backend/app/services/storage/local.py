from __future__ import annotations

from pathlib import Path

from app.services.storage.base import StorageProvider


class LocalStorageProvider(StorageProvider):
    def __init__(self, root: Path, base_url: str):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.base_url = base_url.rstrip("/")

    def _path(self, key: str) -> Path:
        path = (self.root / key).resolve()
        if not str(path).startswith(str(self.root.resolve())):
            raise ValueError("invalid storage key")
        return path

    def save(self, key: str, data: bytes, content_type: str | None = None) -> str:
        path = self._path(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        return self.url(key)

    def read(self, key: str) -> bytes:
        return self._path(key).read_bytes()

    def delete(self, key: str) -> None:
        path = self._path(key)
        if path.exists():
            path.unlink()

    def url(self, key: str) -> str:
        return f"{self.base_url}/{key}"

    def exists(self, key: str) -> bool:
        return self._path(key).exists()
