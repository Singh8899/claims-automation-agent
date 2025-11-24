import logging
import os

from src.minio.minio import get_file_from_minio

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


def get_client_claim(claim_id: str) -> str:
    try:
        object_path = f"{claim_id}/claim.txt"
        response = get_file_from_minio(object_path)
        claim_text = response.read().decode('utf-8')
        response.close()
        response.release_conn()
        logger.info(f"Claim retrieved for {claim_id}")
        return claim_text
    except Exception as e:
        logger.error(f"Error retrieving claim {claim_id}: {e}")
        raise
