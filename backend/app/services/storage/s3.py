"""S3-compatible storage (AWS S3, MinIO, R2, ...). Requires `boto3` to be installed."""

from __future__ import annotations

from app.services.storage.base import StorageProvider


class S3CompatibleProvider(StorageProvider):
    def __init__(
        self, bucket: str, endpoint_url: str, access_key: str, secret_key: str, region: str = ""
    ):
        try:
            import boto3  # type: ignore
        except ImportError as exc:  # pragma: no cover
            raise RuntimeError("boto3 is required for STORAGE_PROVIDER=s3") from exc
        self.bucket = bucket
        self.endpoint = endpoint_url.rstrip("/")
        self.client = boto3.client(
            "s3",
            endpoint_url=endpoint_url or None,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name=region or None,
        )

    def save(self, key: str, data: bytes, content_type: str | None = None) -> str:
        extra = {"ContentType": content_type} if content_type else {}
        self.client.put_object(Bucket=self.bucket, Key=key, Body=data, **extra)
        return self.url(key)

    def read(self, key: str) -> bytes:
        return self.client.get_object(Bucket=self.bucket, Key=key)["Body"].read()

    def delete(self, key: str) -> None:
        self.client.delete_object(Bucket=self.bucket, Key=key)

    def url(self, key: str) -> str:
        return f"{self.endpoint}/{self.bucket}/{key}"

    def exists(self, key: str) -> bool:
        try:
            self.client.head_object(Bucket=self.bucket, Key=key)
            return True
        except Exception:
            return False
