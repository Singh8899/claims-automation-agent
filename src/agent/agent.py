"""Set up the agent with custom tools"""

import os

from dotenv import find_dotenv, load_dotenv
from langchain.agents import create_agent
from langchain_core.messages import HumanMessage

from .agent_utils import get_client_claim
from .prompt import PROMPT
from .security_filter import OutputValidator, PromptInjectionFilter
from .tools import tools

# Load environment variables from .env file
load_dotenv(find_dotenv())


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

def run_agent_query(claim_id: str):
    """Helper function to run a query with the agent"""

    client_claim = get_client_claim(claim_id)
    # Check for prompt injection
    if prompt_injection_filter.detect_injection(client_claim):
        return "The request cannot be processed, reason  'Potential prompt injection detected'."
    client_claim_with_id = f"###CLAIM_ID###:'f{claim_id}'\n" + "###CLAIM###:\n" + client_claim
    response = agent.invoke({"messages": [HumanMessage(content=client_claim_with_id)]},
                            {"recursion_limit":20})
    # Get the last message in the conversation
    last_message = response["messages"][-1]

    # Check if it's a tool message or AI message
    if hasattr(last_message, 'content') and last_message.content:
        return last_message.content
    
    # If no content, look for tool calls and their results
    messages = response["messages"]
    result_messages = []
    for msg in messages:
        if hasattr(msg, 'content') and msg.content and 'Company' in str(msg.content):
            result_messages.append(str(msg.content))
    message = output_validator.filter_response('\n'.join(result_messages) if result_messages else "No response generated")
    return message
