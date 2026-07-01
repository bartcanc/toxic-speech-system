from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class NotificationCreate(BaseModel):
    user_id : int = 1
    device_id: str = "SafeSound 1st Edition"
    transcription: str
    audio_file_path: str | None = None
    audio_duration_seconds: int = 0

class NotificationResponse(BaseModel):
    id: int
    user_id: Optional[int]
    title: str
    display_title: str
    device_id: str
    transcription: str
    audio_file_path: Optional[str]
    audio_duration_seconds: int
    created_at: datetime
    is_read: bool

    class Config:
        from_attributes = True

class PaginatedNotifications(BaseModel):
    total_records: int
    skip: int
    limit: int
    data: List[NotificationResponse]
    
class UpdateTitleRequest(BaseModel):
    title: str