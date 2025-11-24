import logging
import os

from minio import Minio

MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "minio:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "minio_user")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "minio_password_123")
MINIO_BUCKET_NAME = os.getenv("MINIO_BUCKET_NAME", "claims-bucket")
MINIO_SECURE = os.getenv("MINIO_SECURE", "False").lower() == "true"

logger = logging.getLogger(__name__)


class MinIOClient:
    _instance = None
    _client = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MinIOClient, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._client is None:
            self._initialize_client()
    
    def _initialize_client(self):
        try:
            self._client = Minio(
                MINIO_ENDPOINT,
                access_key=MINIO_ACCESS_KEY,
                secret_key=MINIO_SECRET_KEY,
                secure=MINIO_SECURE
            )
            logger.info(f"MinIO client initialized: {MINIO_ENDPOINT}")
            
            if not self._client.bucket_exists(MINIO_BUCKET_NAME):
                self._client.make_bucket(MINIO_BUCKET_NAME)
                logger.info(f"MinIO bucket '{MINIO_BUCKET_NAME}' created successfully")
            else:
                logger.info(f"MinIO bucket '{MINIO_BUCKET_NAME}' already exists")
                
        except Exception as e:
            logger.error(f"Failed to initialize MinIO client: {e}")
            raise
    
    def get_client(self):
        return self._client


# Global client instance
minio_client = MinIOClient().get_client()
