from enum import Enum
from typing import List, Optional

from pydantic import BaseModel


class ClaimDecision(str, Enum):
    UNCERTAIN = "UNCERTAIN"
    APPROVE = "APPROVE"
    DENY = "DENY"

class ClaimDecisionResponse(BaseModel):
    decision : ClaimDecision
    explanation : Optional[str] = None

class ClaimsListResponse(BaseModel):
    claims : List[str]
