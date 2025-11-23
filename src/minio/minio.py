import logging
import os
from io import BytesIO

from fastapi import UploadFile

from minio.error import S3Error

from .client import minio_client

MINIO_BUCKET_NAME = os.getenv("MINIO_BUCKET_NAME", "claims-bucket")

logger = logging.getLogger(__name__)


async def upload_file_to_minio(file: UploadFile, claim_id: int) -> str:
    try:
        object_name = f"{claim_id}/{file.filename}"
        file_data = await file.read()
        
        minio_client.put_object(
            bucket_name=MINIO_BUCKET_NAME,
            object_name=object_name,
            data=BytesIO(file_data),
            length=len(file_data),
            content_type=file.content_type
        )
        
        logger.info(f"File uploaded: {object_name}")
        return object_name
    
    except S3Error as e:
        logger.error(f"S3 Error during upload: {e}")
        raise
    except Exception as e:
        logger.error(f"Error during file upload: {e}")
        raise


async def get_file_from_minio(object_path: str):
    try:
        response = minio_client.get_object(MINIO_BUCKET_NAME, object_path)
        logger.info(f"File retrieved: {object_path}")
        return response
    except S3Error as e:
        logger.error(f"Error retrieving file: {e}")
        raise
    except Exception as e:
        logger.error(f"Error retrieving file: {e}")
        raise


async def delete_file_from_minio(object_path: str) -> bool:
    try:
        minio_client.remove_object(MINIO_BUCKET_NAME, object_path)
        logger.info(f"File deleted: {object_path}")
        return True
    except S3Error as e:
        logger.error(f"Error deleting file: {e}")
        raise
    except Exception as e:
        logger.error(f"Error deleting file: {e}")
        raise


async def list_files_in_minio(claim_id: int):
    try:
        prefix = f"{claim_id}/"
        objects = minio_client.list_objects(MINIO_BUCKET_NAME, prefix=prefix)
        file_list = [obj.object_name for obj in objects]
        logger.info(f"Listed {len(file_list)} files for claim {claim_id}")
        return file_list
    except S3Error as e:
        logger.error(f"Error listing files: {e}")
        raise
    except Exception as e:
        logger.error(f"Error listing files: {e}")
        raise
