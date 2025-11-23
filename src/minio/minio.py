import logging
from io import BytesIO

from fastapi import UploadFile
from PIL import Image

from minio.error import S3Error

from .client import MINIO_BUCKET_NAME, minio_client

# Configure logging
logger = logging.getLogger("src.minio")

# Supported image formats for upload
SUPPORTED_IMAGE_FORMATS = {'.webp', '.jpg', '.jpeg', '.png', '.bmp', '.tiff'}


def convert_image_to_webp(file_data: bytes, original_filename: str) -> bytes:
    try:
        image = Image.open(BytesIO(file_data))
        
        if image.mode in ('RGBA', 'LA', 'P'):
            background = Image.new('RGB', image.size, (255, 255, 255))
            if image.mode == 'P':
                image = image.convert('RGBA')
            background.paste(image, mask=image.split()[-1] if image.mode in ('RGBA', 'LA') else None)
            image = background
        elif image.mode != 'RGB':
            image = image.convert('RGB')
        
        webp_buffer = BytesIO()
        image.save(webp_buffer, format='WebP', quality=85)
        webp_buffer.seek(0)
        
        logger.info(f"Image converted to WebP: {original_filename}")
        return webp_buffer.getvalue()
    
    except Exception as e:
        logger.error(f"Error converting image to WebP: {e}", exc_info=True)
        raise


async def upload_file_to_minio(file: UploadFile, claim_id: int, filename: str = None) -> str:
    try:
        name = filename or file.filename
        file_data = await file.read()
        
        # Convert images to WebP format
        if name.lower().endswith(tuple(SUPPORTED_IMAGE_FORMATS)):
            logger.info(f"Converting image to WebP: {name}")
            file_data = convert_image_to_webp(file_data, name)
            name = name.rsplit('.', 1)[0] + '.webp'
        
        object_name = f"{claim_id}/{name}"
        
        logger.info(f"Uploading file: {object_name}")
        
        minio_client.put_object(
            bucket_name=MINIO_BUCKET_NAME,
            object_name=object_name,
            data=BytesIO(file_data),
            length=len(file_data),
            content_type='image/webp' if name.endswith('.webp') else file.content_type
        )
        
        logger.info(f"File uploaded successfully: {object_name}")
        return object_name
    
    except S3Error as e:
        logger.error(f"S3 Error during upload: {e}", exc_info=True)
        raise
    except Exception as e:
        logger.error(f"Error during file upload: {e}", exc_info=True)
        raise


def get_file_from_minio(object_path: str):
    try:
        response = minio_client.get_object(MINIO_BUCKET_NAME, object_path)
        logger.info(f"File retrieved: {object_path}")
        return response
    except (S3Error, Exception) as e:
        logger.error(f"Error retrieving file {object_path}: {e}")
        raise


def get_file_from_minio_sync(object_path: str):
    return get_file_from_minio(object_path)


def get_image_from_minio(claim_id: str) -> bytes:
    try:
        object_path = f"{claim_id}/image.webp"
        response = minio_client.get_object(MINIO_BUCKET_NAME, object_path)
        image_bytes = response.read()
        response.close()
        response.release_conn()
        logger.info(f"Image retrieved for claim {claim_id}")
        return image_bytes
    except (S3Error, Exception) as e:
        logger.error(f"Error retrieving image for claim {claim_id}: {e}")
        raise


def get_claim_metadata(claim_id: str) -> str:
    try:
        metadata_path = f"{claim_id}/metadata.md"
        response = minio_client.get_object(MINIO_BUCKET_NAME, metadata_path)
        metadata_content = response.read().decode("utf-8")
        response.close()
        response.release_conn()
        logger.info(f"Metadata retrieved for claim {claim_id} ({len(metadata_content)} characters)")
        return metadata_content
    except (S3Error, Exception) as e:
        logger.error(f"Error retrieving metadata for claim {claim_id}: {e}")
        raise


async def delete_file_from_minio(object_path: str) -> bool:
    try:
        minio_client.remove_object(MINIO_BUCKET_NAME, object_path)
        logger.info(f"File deleted: {object_path}")
        return True
    except (S3Error, Exception) as e:
        logger.error(f"Error deleting file {object_path}: {e}")
        raise


async def list_files_in_minio(claim_id: int):
    try:
        prefix = f"{claim_id}/"
        objects = minio_client.list_objects(MINIO_BUCKET_NAME, prefix=prefix)
        file_list = [obj.object_name for obj in objects]
        logger.info(f"Listed {len(file_list)} files for claim {claim_id}")
        return file_list
    except (S3Error, Exception) as e:
        logger.error(f"Error listing files for claim {claim_id}: {e}")
        raise
