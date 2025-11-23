""""Utility functions for the agent"""
import logging
import os
from io import BytesIO

from minio.error import S3Error
from src.minio.client import minio_client

logger = logging.getLogger("src.agent")

def get_policy_document() -> str:
    policy_path = os.path.join(
        os.path.dirname(__file__),
        "..",
        "policy",
        "policy.md"
    )
    
    try:
        with open(policy_path, "r", encoding="utf-8") as f:
            policy_text = f.read()
        logger.info(f"Policy document retrieved successfully ({len(policy_text)} characters)")
        return policy_text
    except FileNotFoundError:
        logger.error(f"Policy document not found at {policy_path}")
        raise
    except Exception as e:
        logger.error(f"Error reading policy document: {e}")
        raise


def get_client_claim(claim_id: int) -> str:
    try:
        bytesio_claim = retrieve_file_from_minio(f"{claim_id}/claim.txt")
        return bytesio_claim.read().decode('utf-8')
    except (UnicodeDecodeError, Exception) as e:
        logger.error(f"Error retrieving claim {claim_id}: {e}")
        raise

def retrieve_file_from_minio(object_path: str) -> BytesIO:
    bucket_name = os.getenv("MINIO_BUCKET_NAME", "claims-bucket")
    try:
        response = minio_client.get_object(bucket_name, object_path)
        file_data = BytesIO(response.read())
        response.close()
        response.release_conn()
        return file_data
    except (S3Error, Exception) as e:
        logger.error(f"Error retrieving {object_path}: {e}")
        raise
