import os

import uvicorn
from dotenv import find_dotenv, load_dotenv

from src.api.app import app
from src.minio.client import MinIOClient

# Load environment variables from .env file
load_dotenv(find_dotenv())


def main():
    # Initialize Minio Client
    MinIOClient()
    
    # Run the API server
    uvicorn.run(
        app,
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", 8000)),
        log_level="info"
    )


if __name__ == "__main__":
    main()
