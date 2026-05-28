from pydantic import BaseModel
from typing import List
# input
class TextRequest(BaseModel):
    text: str

# output
class ConfidenceScores(BaseModel):
    toxic: float
    scam: float
    grooming: float

class AIResults(BaseModel):
    is_safe: bool
    detected_flags: List[str]
    confidence_scores: ConfidenceScores

class AnalysisResponse(BaseModel):
    status: str
    text_analyzed: str
    results: AIResults

# device
class DevicePing(BaseModel):
    device_id: str
    status: str = "active"