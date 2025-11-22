import os
from minio import Minio
from minio.error import S3Error
from fastapi import UploadFile

# MinIO Configuration 
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "minio:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "minio_user")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "minio_password_123")
MINIO_BUCKET_NAME = os.getenv("MINIO_BUCKET_NAME", "claims-bucket")

# Initialize the MinIO Client
try:
    minio_client = Minio(
        MINIO_ENDPOINT,
        access_key=MINIO_ACCESS_KEY,
        secret_key=MINIO_SECRET_KEY,
        secure=False # True in production with SSL
    )
except Exception as e:
    print(f"Failed to initialize MinIO client: {e}")

# Check and create the bucket on startup
if not minio_client.bucket_exists(MINIO_BUCKET_NAME):
    try:
        minio_client.make_bucket(MINIO_BUCKET_NAME)
        print(f"MinIO bucket '{MINIO_BUCKET_NAME}' created successfully.")
    except S3Error as e:
        print(f"Error creating MinIO bucket: {e}")

def upload_file_to_minio(file: UploadFile, claim_id: int) -> str:
    try:
        # Create a unique object name based on claim ID and file type
        object_name = f"{claim_id}/{file.filename}"
        
        file.file.seek(0)
        
        # Upload the file object
        minio_client.put_object(
            bucket_name=MINIO_BUCKET_NAME,
            object_name=object_name,
            data=file.file,
            length=file.size,
            content_type=file.content_type
        )
        
        return object_name
    
    except S3Error as e:
        print(f"S3 Error during MinIO upload: {e}")
        raise
    except Exception as e:
        print(f"General error during MinIO upload: {e}")
        raise


def get_file_from_minio(object_path: str):
    try:
        response = minio_client.get_object(MINIO_BUCKET_NAME, object_path)
        return response
    except S3Error as e:
        print(f"Error retrieving file from MinIO: {e}")
        raise
