""""Utility functions for the agent"""
import os
from io import BytesIO

from minio import Minio
from minio.error import S3Error

# Initialize the MinIO client using environment variables from docker-compose.yml
MINIO_CLIENT = Minio(
    os.getenv("MINIO_ENDPOINT"), 
    access_key=os.getenv("MINIO_ACCESS_KEY"),
    secret_key=os.getenv("MINIO_SECRET_KEY"),
    secure=False # Use False for local Docker setup
)

def get_client_claim(claim_id: int):
    bytesio_claim = retrieve_file_from_minio(claim_id+"/claim.txt")
    try:
        file_bytes = bytesio_claim.read()
        file_string = file_bytes.decode('utf-8')
    
        return file_string
        
    except UnicodeDecodeError as e:
        print(f"Error decoding bytes: Check the file's encoding! {e}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred during conversion: {e}")
        return None

def retrieve_file_from_minio(object_path: str):
    """
    Retrieves the file object from MinIO based on its stored path.
    """
    bucket_name = os.getenv("MINIO_BUCKET_NAME") # claims-bucket
    
    try:
        response = MINIO_CLIENT.get_object(bucket_name, object_path)
        file_data = BytesIO(response.read())
        response.close()
        response.release_conn() 
        
        return file_data # This contains the raw bytes of the file (image, text, etc.)
        
    except S3Error as e:
        print(f"Error retrieving file from MinIO: {e}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return None
