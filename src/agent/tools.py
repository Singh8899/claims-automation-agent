from langchain_core.tools import tool

from src.agent.agent_utils import get_policy_document
from src.minio.minio import get_claim_metadata, get_image_from_minio
from src.utils.schemas import ClaimDecision, ClaimDecisionResponse
from src.utils.vision_analyzer import query_image_forgery, query_image_ocr


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
    Extracts textual information from claim documents using OCR vision model.
    Use this tool to READ and EXTRACT information from documents.
    
    Args:
        claim_id: claim id that is being analyzed
        query: The question asking for specific information to extract.
               
               Good examples:
               - "Is this a plain text document on blank page, or an official medical form with letterhead?"
               - "What is the exact patient name shown on this document?"
               - "What dates are mentioned in this document (admission, discharge, consultation, issuance)?"
               - "What medical findings, diagnosis, or fitness statements are written in this document?"
               - "Are there physician signatures visible? Are there hospital stamps visible? Are any critical fields blank?"
        
    Returns:
        Extracted information from the document based on the query
    """
    try:
        image_bytes = get_image_from_minio(claim_id)
        if image_bytes is None:
            return "No image document has been provided by the user for this claim."
        image_info = query_image_ocr(image_bytes, query)
        return image_info
    except Exception as e:
        return f"Error retrieving/analyzing image for claim {claim_id}: {str(e)}"

@tool
def check_image_forgery(claim_id: str, query: str) -> str:
    """
    Analyzes document authenticity and detects potential forgery or manipulation.
    Use this tool FIRST before extracting information to verify the document is legitimate.
    
    IMPORTANT: Always provide CONTEXT in your query about what document is expected.
    
    Args:
        claim_id: claim id that is being analyzed
        query: Question about document authenticity WITH CONTEXT about the claim.
               
               REQUIRED FORMAT:
               "Analyze this document for authenticity. Context: This claim is for [reason] on [date]. The document should be a [expected document type].
               
               Check for fraud indicators:
               - Is this plain typed text on blank page (NOT acceptable) or official medical form with letterhead?
               - Are there signs of digital manipulation, photoshopped stamps, or overlaid signatures?
               - Are critical fields blank (like 'discharged on ___')?
               - Are date stamps inconsistent or wrong format/year?
               - Does document format match expected type?
               
               Assess: DEFINITIVE FRAUD, SUSPICIOUS, or LEGITIMATE"
               
               Good example:
               "Analyze for authenticity. Context: Medical emergency claim for hospitalization on 2023-08-13. Should be hospital admission/discharge certificate. Check: Is this plain text or official form? Any photoshopped stamps? Blank critical fields? Date inconsistencies? Assess: DEFINITIVE FRAUD, SUSPICIOUS, or LEGITIMATE."
               
               This tool detects:
               - Plain text documents (automatic fraud)
               - Photoshopped/digitally added stamps or signatures
               - Blank critical fields ("discharged on ___", "patient: ___")
               - Inconsistent or anachronistic dating
               - Wrong document type for the claim
        
    Returns:
        Assessment of document authenticity: DEFINITIVE FRAUD, SUSPICIOUS, or LEGITIMATE with specific observations
    """
    try:
        image_bytes = get_image_from_minio(claim_id)
        if image_bytes is None:
            return "No image document has been provided by the user for this claim."
        image_info = query_image_forgery(image_bytes, query)
        return image_info
    except Exception as e:
        return f"Error retrieving/analyzing image for claim {claim_id}: {str(e)}"


tools = [
    check_image_forgery,
    get_policy,
    get_metadata,
    get_info_from_image,
    present_decision
]
