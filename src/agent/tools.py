"""Define custom tools for the agent"""
from langchain_core.tools import tool

from src.minio.minio import get_image_from_minio, get_claim_metadata
from src.agent.agent_utils import get_policy_document
from src.utils.schemas import ClaimDecision, ClaimDecisionResponse
from src.utils.vision_analyzer import query_image


@tool(return_direct=False)
def get_policy() -> str:
    """
    Retrieve the CFSR insurance policy document to reference during claim analysis.
    This tool should be called early to understand policy coverage rules.
    
    Returns:
        Full policy text including covered reasons, requirements, and exclusions
    """
    try:
        policy_text = get_policy_document()
        return policy_text
    except Exception as e:
        return f"Error retrieving policy: {str(e)}"


@tool(return_direct=False)
def get_metadata(claim_id: str) -> str:
    """
    Retrieve claim metadata (booking details, dates, amounts, etc.) from storage.
    Should be called to get additional context about the claim.
    
    Args:
        claim_id: The unique identifier for the claim
    
    Returns:
        Metadata content containing booking information and claim details
    """
    try:
        metadata = get_claim_metadata(claim_id)
        return metadata
    except Exception as e:
        return f"Error retrieving metadata for claim {claim_id}: {str(e)}"


@tool(return_direct=True)
def present_decision(decision: ClaimDecision, explanation: str) -> ClaimDecisionResponse:
    """
    THIS MUST BE THE LAST STEP - call this to complete the workflow.
    
    Args:
        decision: the final decision on the claim (APPROVE, DENY, or UNCERTAIN)
        explanation: a detailed explanation of the decision with policy references
    
    Returns:
        final decision on the claim with explanation
    """
    return ClaimDecisionResponse(decision=decision, explanation=explanation)


@tool
def get_info_from_image(claim_id: str, query: str) -> str:
    """
    Retrieves textual information from claim documents using vision model.
    Can be called multiple times for different documents or different queries.
    
    Args:
        claim_id: claim id that is being analyzed
        query: The detailed question to ask the vision model about the document
               Should ask specifically about required information like:
               - Document type and authenticity
               - Dates and amounts
               - Required signatures or stamps
               - Names and reference numbers
        
    Returns:
        Information extracted from the image document
    """
    try:
        image_bytes = get_image_from_minio(claim_id)
        image_info = query_image(image_bytes, query)
        return image_info
    except Exception as e:
        return f"Error retrieving/analyzing image for claim {claim_id}: {str(e)}"


# List of tools to be used by the agent
tools = [
    get_policy,
    get_metadata,
    get_info_from_image,
    present_decision
]
