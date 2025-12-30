from pydantic import BaseModel
from typing import List, Optional

class ClaimRequest(BaseModel):
    claim: str

class Evidence(BaseModel):
    text: str
    source: str
    url: Optional[str] = None
    confidence: float

class VerificationResult(BaseModel):
    claim: str
    verdict: str  # "Supported", "Refuted", "NotEnoughInfo"
    reasoning: str
    evidence: List[Evidence]
