import logging
import os
from io import BytesIO

from fastapi import UploadFile

from minio.error import S3Error

from .client import minio_client

MINIO_BUCKET_NAME = os.getenv("MINIO_BUCKET_NAME", "claims-bucket")

# Configure logging
logger = logging.getLogger("src.minio")
logger.setLevel(logging.INFO)


async def upload_file_to_minio(file: UploadFile, claim_id: int, filename: str = None) -> str:
    try:
        name = filename or file.filename
        object_name = f"{claim_id}/{name}"
        file_data = await file.read()
        
        logger.info(f"Uploading file: {object_name}")
        
        minio_client.put_object(
            bucket_name=MINIO_BUCKET_NAME,
            object_name=object_name,
            data=BytesIO(file_data),
            length=len(file_data),
            content_type=file.content_type
        )
        
        logger.info(f"File uploaded successfully: {object_name}")
        return object_name
    
    except S3Error as e:
        logger.error(f"S3 Error during upload: {e}", exc_info=True)
        raise
    except Exception as e:
        logger.error(f"Error during file upload: {e}", exc_info=True)
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


def get_image_from_minio(claim_id: str) -> bytes:
    try:
        object_path = f"{claim_id}/image.jpg"
        response = minio_client.get_object(MINIO_BUCKET_NAME, object_path)
        image_bytes = response.read()
        response.close()
        response.release_conn()
        logger.info(f"Image retrieved for claim {claim_id}")
        return image_bytes
    except S3Error as e:
        logger.error(f"Error retrieving image for claim {claim_id}: {e}")
        raise
    except Exception as e:
        logger.error(f"Error retrieving image for claim {claim_id}: {e}")
        raise


def get_file_from_minio_sync(object_path: str):
    try:
        response = minio_client.get_object(MINIO_BUCKET_NAME, object_path)
        logger.info(f"File retrieved: {object_path}")
        return response
    except S3Error as e:
        logger.error(f"Error retrieving file {object_path}: {e}")
        raise
    except Exception as e:
        logger.error(f"Error retrieving file {object_path}: {e}")
        raise


def get_claim_metadata(claim_id: str) -> str:
    """
    Retrieve claim metadata from MinIO.
    
    Args:
        claim_id: The claim identifier
    
    Returns:
        Metadata content as string
    
    Raises:
        Exception: If metadata retrieval fails
    """
    try:
        metadata_path = f"{claim_id}/metadata.md"
        response = get_file_from_minio_sync(metadata_path)
        
        if response is None:
            logger.warning(f"Metadata not found for claim {claim_id}")
            return "No metadata available"
        
        metadata_content = response.read().decode("utf-8")
        logger.info(f"Metadata retrieved for claim {claim_id} ({len(metadata_content)} characters)")
        return metadata_content
        
    except Exception as e:
        logger.error(f"Error retrieving metadata for claim {claim_id}: {e}")
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
