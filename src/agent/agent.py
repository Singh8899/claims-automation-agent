"""Set up the agent with custom tools"""

import logging
import os
import re

from dotenv import find_dotenv, load_dotenv
from langchain.agents import create_agent
from langchain_core.messages import HumanMessage

from .agent_utils import get_client_claim
from .prompt import PROMPT
from .security_filter import OutputValidator, PromptInjectionFilter
from .tools import tools

# Load environment variables from .env file
load_dotenv(find_dotenv())

logger = logging.getLogger("src.agent")


# Initialize the prompt injection filter
prompt_injection_filter = PromptInjectionFilter()

# Initialize the output validator
output_validator = OutputValidator()



# Create the React agent
agent = create_agent(
    model="gpt-5-mini",
    tools=tools,
    system_prompt=PROMPT
)

def run_agent_query(claim_id: str) -> dict:
    """Helper function to run a query with the agent"""

    client_claim = get_client_claim(claim_id)
    # Check for prompt injection
    if prompt_injection_filter.detect_injection(client_claim):
        return {"decision": "DENY", "explanation": "Potential prompt injection detected", "claim_id": claim_id}
    
    # Format claim with correct ID (no extra 'f' prefix)
    client_claim_with_id = f"###CLAIM_ID###:{claim_id}\n###CLAIM###:\n{client_claim}"
    
    try:
        response = agent.invoke(
            {"messages": [HumanMessage(content=client_claim_with_id)]},
            {"recursion_limit": int(os.getenv("RECURSION_LIMIT", 20))}
        )
        
        # Extract the final message from the response
        final_message = response["messages"][-1].content if response.get("messages") else ""
        
        # Validate the output for security issues
        validated_response = output_validator.filter_response(final_message)
        
        # Parse decision from ClaimDecision enum format: decision=<ClaimDecision.DENY: 'DENY'>
        decision_enum_match = re.search(
            r'decision=<ClaimDecision\.(\w+):\s*[\'"](\w+)[\'"]>',
            final_message
        )
        
        if decision_enum_match:
            decision = decision_enum_match.group(2).upper()
        else:
            # Fallback: Parse plain decision strings
            decision_match = re.search(
                r'\*?\*?(?:APPROVE|DENY|UNCERTAIN)\*?\*?',
                final_message,
                re.IGNORECASE
            )
            decision = decision_match.group(0).upper().replace("*", "") if decision_match else None
        
        # Parse explanation from response
        explanation_match = re.search(
            r"explanation='([^']*)'|explanation=\"([^\"]*)\"",
            final_message
        )
        explanation = explanation_match.group(1) or explanation_match.group(2) if explanation_match else validated_response
        
        if decision:
            logger.info(f"Agent decision for claim {claim_id}: {decision}")
            return {
                "decision": decision,
                "explanation": explanation,
                "claim_id": claim_id
            }
        else:
            logger.warning(f"Could not parse decision for claim {claim_id}")
            return {
                "decision": "UNCERTAIN",
                "explanation": "Could not parse a valid decision from agent response",
                "claim_id": claim_id
            }
        
    except Exception as e:
        logger.error(f"Error in agent processing: {str(e)}", exc_info=True)
        return {"decision": "UNCERTAIN", "explanation": f"Agent processing error: {str(e)}", "claim_id": claim_id}
