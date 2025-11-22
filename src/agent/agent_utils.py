""""Utility functions for the agent"""
import ast
import json
import os
import re
from io import BytesIO

from minio import Minio
from minio.error import S3Error

from .template_content import Content


def parse_content(content_str: str):
    """Parse content string whether it's JSON or Python dict format"""

    if isinstance(content_str, str):
        content_str = content_str.strip()

        try:
            # Try JSON first
            return json.loads(content_str)
        except json.JSONDecodeError:
            try:
                # Try Python literal eval
                return ast.literal_eval(content_str)
            except (ValueError, SyntaxError):
                try:
                    fixed_str = re.sub(r"'([^']*)':", r'"\1":', content_str)  # Fix keys
                    fixed_str = re.sub(r": '([^']*)'", r': "\1"', fixed_str)   # Fix values
                    return json.loads(fixed_str)
                except:
                    raise ValueError("Could not parse content string as JSON or Python dict")
    elif isinstance(content_str, dict):
        return content_str
    elif isinstance(content_str, Content):
        return content_str.model_dump()
    
def get_file_path_from_db(claim_id: int, file_type: str):
    """
    Finds the stored MinIO object path for a specific claim and file type.
    """
    # This is a conceptual query. In real SQLAlchemy, you'd query a Model.
    claim_record = db_session.execute(
        f"SELECT {file_type}_path FROM claims WHERE claim_id = :id", 
        {"id": claim_id}
    ).fetchone()

    if claim_record:
        # Returns the path, e.g., 'claims-bucket/123/image.webp'
        return claim_record[0]
    return None

# Initialize the MinIO client using environment variables from docker-compose.yml
MINIO_CLIENT = Minio(
    os.getenv("MINIO_ENDPOINT"), 
    access_key=os.getenv("MINIO_ACCESS_KEY"),
    secret_key=os.getenv("MINIO_SECRET_KEY"),
    secure=False # Use False for local Docker setup
)

def retrieve_file_from_minio(object_path: str):
    """
    Downloads the file object from MinIO based on its stored path.
    """
    bucket_name = os.getenv("MINIO_BUCKET_NAME") # claims-bucket
    # The object path should be the part after the bucket name
    
    try:
        # 1. Get the object data
        response = MINIO_CLIENT.get_object(bucket_name, object_path)
        
        # 2. Read the entire object data into memory (BytesIO is efficient)
        file_data = BytesIO(response.read())
        
        # 3. IMPORTANT: Close the response stream
        response.close()
        response.release_conn() 
        
        return file_data # This contains the raw bytes of the file (image, text, etc.)
        
    except S3Error as e:
        print(f"Error retrieving file from MinIO: {e}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return None