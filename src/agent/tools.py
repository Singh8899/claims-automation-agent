"""Define custom tools for the agent"""
from langchain_core.tools import tool

from utils.schemas import ClaimDecision, ClaimDecisionResponse
from utils.vision_analyzer import query_image


@tool(return_direct=True)
def present_decision(decision: ClaimDecision, explanation: str) ->  ClaimDecisionResponse:
    """
    THIS MUST BE THE LAST STEP - call this to complete the workflow.
    Args:
        decision: the final decision on the claim
        explanation: a brief reason that conducted to that decision
    Returns:
        final decision on the claim with a brief explanation
    """

    return ClaimDecisionResponse(decision=decision, explanation= explanation)


@tool
def get_info_from_image(claim_id: str, query: str) -> str:
    """Retrieves textual info from the document using a VLM
        Can be called multiple time if necessary.
    
    Args:
        claim_id: claim id that is being analyzed
        query: The query to ask to the vision model about the image document, 
                should be detailed and asking clearly what is needed to understan 
                if the claim from the user is real or fake.
        
    Returns:
        Information retrived from the image
    """
    image_bytes = get_image_from_minio(claim_id)
    image_info = query_image(image_bytes, query)
    return image_info



# List of tools to be used by the agent
tools = [
    get_info_from_image,
    present_decision
]
