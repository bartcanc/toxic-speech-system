from pydantic import BaseModel

class TextRequest(BaseModel):
    text: str

class AnalysisResponse(BaseModel):
    text: str
    verdict: str
    confidence_percent: float

class DevicePing(BaseModel):
    device_id: str
    status: str = "active"