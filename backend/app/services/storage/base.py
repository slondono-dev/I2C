from __future__ import annotations

from abc import ABC, abstractmethod


class StorageProvider(ABC):
    """Abstract file storage. Keys are relative paths like 'products/<id>/original.jpg'."""

    @abstractmethod
    def save(self, key: str, data: bytes, content_type: str | None = None) -> str:
        """Store bytes and return a public URL."""

    @abstractmethod
    def read(self, key: str) -> bytes: ...

    @abstractmethod
    def delete(self, key: str) -> None: ...

    @abstractmethod
    def url(self, key: str) -> str: ...

    @abstractmethod
    def exists(self, key: str) -> bool: ...
