import os
import logging
from typing import Optional, Tuple
from services.api.app.core.config import settings

logger = logging.getLogger("ai_qa_agent.storage")

class StorageService:
    def __init__(self):
        self.endpoint_url = settings.r2_endpoint_url
        self.access_key = settings.r2_access_key
        self.secret_key = settings.r2_secret_key
        self.bucket_name = settings.r2_bucket
        self.region = settings.S3_REGION or "auto"
        self.public_prefix = settings.S3_PUBLIC_URL_PREFIX
        self.local_storage_dir = "./artifacts_storage"
        os.makedirs(self.local_storage_dir, exist_ok=True)

        self._s3_client = None
        if self.is_r2_configured:
            try:
                import boto3
                from botocore.config import Config

                self._s3_client = boto3.client(
                    "s3",
                    endpoint_url=self.endpoint_url,
                    aws_access_key_id=self.access_key,
                    aws_secret_access_key=self.secret_key,
                    region_name=self.region,
                    config=Config(signature_version="s3v4")
                )
                logger.info(f"Cloudflare R2 / S3 storage initialized on bucket: {self.bucket_name}")
            except Exception as e:
                logger.warning(f"Failed to initialize S3/R2 client: {e}. Falling back to local disk.")
                self._s3_client = None

    @property
    def is_r2_configured(self) -> bool:
        return bool(self.endpoint_url and self.access_key and self.secret_key)

    def upload_file(self, local_path: str, destination_key: str, content_type: Optional[str] = None) -> str:
        """
        Uploads a file to Cloudflare R2 if configured, otherwise stores locally.
        Returns the storage path or S3 key.
        """
        if self._s3_client:
            try:
                extra_args = {}
                if content_type:
                    extra_args["ContentType"] = content_type

                self._s3_client.upload_file(
                    Filename=local_path,
                    Bucket=self.bucket_name,
                    Key=destination_key,
                    ExtraArgs=extra_args if extra_args else None
                )
                logger.info(f"Successfully uploaded {destination_key} to R2 bucket {self.bucket_name}")
                return f"s3://{self.bucket_name}/{destination_key}"
            except Exception as e:
                logger.error(f"Error uploading to R2: {e}. Keeping local file {local_path}")
                return local_path
        
        # Local fallback
        return local_path

    def get_presigned_download_url(self, s3_key: str, expires_in: int = 3600) -> Optional[str]:
        """
        Generates a temporary presigned URL for downloading the artifact from R2.
        """
        if self.public_prefix:
            clean_key = s3_key.replace(f"s3://{self.bucket_name}/", "").lstrip("/")
            return f"{self.public_prefix.rstrip('/')}/{clean_key}"

        if self._s3_client:
            try:
                clean_key = s3_key.replace(f"s3://{self.bucket_name}/", "").lstrip("/")
                url = self._s3_client.generate_presigned_url(
                    "get_object",
                    Params={"Bucket": self.bucket_name, "Key": clean_key},
                    ExpiresIn=expires_in
                )
                return url
            except Exception as e:
                logger.error(f"Failed to generate presigned URL for {s3_key}: {e}")
                return None
        return None

storage_service = StorageService()
