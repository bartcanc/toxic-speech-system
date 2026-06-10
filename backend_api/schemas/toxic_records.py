from pydantic import BaseModel
from typing import List, Optional, Any
from datetime import datetime

class ToxicRecordResponse(BaseModel):
    id: int
    text_input: str
    raw_ai_results: Any
    triggered_flag: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True

class PaginatedToxicRecords(BaseModel):
    total_records: int
    skip: int
    limit: int
    data: List[ToxicRecordResponse]