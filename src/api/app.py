import logging
import sys
import uuid
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, File, HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from src.agent.agent import run_agent_query
from src.minio.minio import upload_file_to_minio
from src.postgreql import crud
from src.postgreql.session import get_db, lifespan
from src.utils.schemas import ClaimDecisionResponse, ClaimsListResponse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)

logger = logging.getLogger("src.api.app")
logger.setLevel(logging.INFO)


@asynccontextmanager
async def app_lifespan(app: FastAPI):
    """Application lifespan with startup and shutdown"""
    async with lifespan():
        yield


app = FastAPI(
    title="Insurance claims processor API",
    description="API for processing insurance claims from clients",
    lifespan=app_lifespan
)


@app.get("/")
async def root():
    return {
        "message": "Insurance claims processor API",
        "docs": "/docs"
    }


@app.post("/claims", response_model=dict)
async def process_claim(
    claim_message: UploadFile = File(..., description="User claim (.txt file)"),
    claim_metadata: UploadFile = File(..., description="User metadata (.md file)"),
    claim_image: UploadFile = File(None, description="Image supporting the claim (.webp, .jpg, .jpeg, .png, .bmp, .tiff) - Optional"),
    db: AsyncSession = Depends(get_db)
):
    claim_id = str(uuid.uuid4())
    
    try:
        logger.info(f"Processing new claim: {claim_id}")
        logger.info(f"Uploading claim documents")
        
        # Upload claim message with standardized name
        message_path = await upload_file_to_minio(claim_message, claim_id, "claim.txt")
        metadata_path = await upload_file_to_minio(claim_metadata, claim_id, "metadata.md")
        
        image_path = None
        if claim_image:
            image_path = await upload_file_to_minio(claim_image, claim_id, "image.webp")
            logger.info(f"Files uploaded for claim {claim_id}: {message_path}, {metadata_path}, {image_path}")
        else:
            logger.info(f"Files uploaded for claim {claim_id}: {message_path}, {metadata_path} (no image provided)")

        response = await run_agent_query(claim_id)
        
        decision = response.decision.value  # Convert enum to string
        explanation = response.explanation or ""
        
        # Save claim decision to database
        await crud.create_claim(
            db=db,
            claim_id=claim_id,
            decision=decision,
            explanation=explanation
        )
        
        logger.info(f"Claim {claim_id} processed with decision: {decision}")
        
        return {
            "message": f"Claim submitted successfully",
            "claim_id": claim_id,
            "decision": decision,
            "explanation" : explanation
        }
        
    except Exception as e:
        logger.error(f"Error processing claim: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Claim submission failed: {str(e)}"
        )


@app.get("/claims/{claim_id}", response_model=ClaimDecisionResponse)
async def get_claim_result(
    claim_id: str,
    db: AsyncSession = Depends(get_db)
):
    try:
        db_claim = await crud.get_claim_by_id(db, claim_id)
        
        if not db_claim:
            raise HTTPException(
                status_code=404,
                detail=f"Claim {claim_id} not found"
            )
        
        return ClaimDecisionResponse(
            decision=db_claim.decision,
            explanation=db_claim.explanation
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving claim {claim_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving claim: {str(e)}"
        )


@app.get("/claims", response_model=ClaimsListResponse)
async def get_claims(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    try:
        claims = await crud.get_all_claims(db, skip=skip, limit=limit)
        claim_ids = [claim.claim_id for claim in claims]
        
        return ClaimsListResponse(claims=claim_ids)
        
    except Exception as e:
        logger.error(f"Error retrieving claims: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving claims: {str(e)}"
        )
