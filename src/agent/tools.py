"""Define custom tools for the agent"""
from langchain_core.tools import tool

from src.agent.agent_utils import get_policy_document
from src.minio.minio import get_claim_metadata, get_image_from_minio
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
        explanation: a brief explanation of the decision (max 2-3 sentences)
    
    Returns:
        final decision on the claim with explanation
    """
    return ClaimDecisionResponse(decision=decision, explanation=explanation)


@tool
def get_info_from_image(claim_id: str, query: str) -> str:
    """
    Retrieves textual information from claim documents using vision model.
    Can be called multiple times for different information from the document.
    
    Args:
        claim_id: claim id that is being analyzed
        query: The detailed question to ask the vision model about the document
               Examples of useful queries:
               - "What type of document is this? Is it a scanned/printed document or plain text?"
               - "What is the patient name on this document?"
               - "What dates are mentioned? Extract admission date, discharge date, certificate date."
               - "What medical condition or diagnosis is stated?"
               - "Does this state the patient is fit/healthy or unfit to travel?"
               - "Is there a physician signature and hospital stamp visible?"
        
    Returns:
        Information extracted from the image document, or a message if no image was provided
    """
    try:
        image_bytes = get_image_from_minio(claim_id)
        if image_bytes is None:
            return "No image document has been provided by the user for this claim."
        image_info = query_image(image_bytes, query)
        return image_info
    except Exception as e:
        return f"Error retrieving/analyzing image for claim {claim_id}: {str(e)}"


tools = [
    get_policy,
    get_metadata,
    get_info_from_image,
    present_decision
]
