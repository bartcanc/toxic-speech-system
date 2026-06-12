from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import Optional, List

from core.database import get_db
from models.tables import ToxicRecord, User
from schemas.toxic_records import ToxicRecordResponse, PaginatedToxicRecords

from core.auth import get_current_admin, get_current_user

router = APIRouter(
    prefix="/api/toxic-records",
    tags=["Toxic Records"]
)

@router.get("", response_model=PaginatedToxicRecords)
def get_toxic_records(
    skip: int = Query(0, ge=0, description="ile rekordow pominac"),
    limit: int = Query(50, ge=1, le=100, description="ile rekordow pobrac naraz"),
    flag: Optional[str] = Query(None, description="filtruj po fladze, np. 'toxic', 'grooming', 'scam'"),
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    query = db.query(ToxicRecord)
    
    if flag:
        query = query.filter(ToxicRecord.triggered_flag == flag)
        
    total = query.count()
    
    records = query.order_by(ToxicRecord.created_at.desc()).offset(skip).limit(limit).all()
    
    return {
        "total_records": total,
        "skip": skip,
        "limit": limit,
        "data": records
    }

@router.get("/user_records/{id}", response_model=ToxicRecordResponse)
def get_toxic_record_by_id(
    id: int, 
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    record = db.query(ToxicRecord).filter(ToxicRecord.id == id).first()
    
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"Rekord toksycznosci o id {id} nie zostal odnaleziony"
        )
        
    return record

@router.get("/my_records", response_model=List[ToxicRecordResponse])
def get_my_toxic_records(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    records = (
        db.query(ToxicRecord)
        .filter(ToxicRecord.owner_id == current_user.id)
        .order_by(ToxicRecord.created_at.desc())
        .all()
    )
    return records