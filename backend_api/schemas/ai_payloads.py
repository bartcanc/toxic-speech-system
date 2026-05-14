from pydantic import BaseModel

# input
class TextRequest(BaseModel):
    text: str

# output
class AnalysisResponse(BaseModel):
    text: str
    verdict: str
    confidence_percent: float

# device
class DevicePing(BaseModel):
    device_id: str
    status: str = "active"