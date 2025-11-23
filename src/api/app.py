from fastapi import FastAPI, File, UploadFile

from src.agent.agent import run_agent_query
from utils.schemas import ClaimDecisionResponse, ClaimsListResponse

app = FastAPI(
    title="Insurance claims processor API",
    description="API for processing insurance claims from clients"
)

@app.get("/")
async def root():
    return {
        "message": "Insurance claims processor API",
        "docs": "/docs"
    }

@app.post("/claims")
async def process_claim(
    claim_message: UploadFile = File(..., description="User claim (.txt file)"),
    claim_metadata: UploadFile = File(..., description="User metadata (.md file)"),
    claim_image: UploadFile = File(..., description="Image supporting the claim (.webp file)")
):
    message_text = await claim_message.read()
    metadata_text = await claim_metadata.read()
    image_bytes = await claim_image.read()
    try:
        claim_id = save_data(message_text, metadata_text, image_bytes)
        response_dict = run_agent_query(claim_id)
        save_response(response_dict)
    # TODO: put proper exceptions
    except Exception:
        return {"message": f"Claim submission failed"}

    return {"message": f"Claim submitted successfully with reference: {claim_id}."}

@app.get("/claims/{claim}", response_model=ClaimDecisionResponse)
async def get_claim_result():
    pass

@app.get("/claims", response_model=ClaimsListResponse)
async def get_claims():
    pass
