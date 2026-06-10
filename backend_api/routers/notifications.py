from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List

from core.database import get_db
from models.tables import Notification
from schemas.notif_schemas import NotificationResponse, UpdateTitleRequest, NotificationCreate, PaginatedNotifications

from pydantic import BaseModel

router = APIRouter(
    prefix="/api/notifications",
    tags=["Notifications"]
)

# TODO: Only logged in users can fetch notifications

@router.post("", response_model=NotificationResponse, status_code=status.HTTP_201_CREATED)
def create_notification(payload: NotificationCreate, db: Session = Depends(get_db)):
    new_notification = Notification(
        user_id=payload.user_id,
        device_name=payload.device_name,
        transcription=payload.transcription,
        audio_file_path=payload.audio_file_path,
        audio_duration_seconds=payload.audio_duration_seconds
    )
    db.add(new_notification)
    db.commit()
    db.refresh(new_notification)
    return new_notification

@router.get("", response_model=PaginatedNotifications)
def get_all_notifications(
    skip: int = Query(0, ge=0, description="ile rekordow pominac"),
    limit: int = Query(10, ge=1, le=100, description="ile rekordow pobrac naraz"),
    db: Session = Depends(get_db)
):
    total = db.query(Notification).count()
    
    notifications = (
        db.query(Notification)
        .order_by(Notification.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    
    return {
        "total_records": total,
        "skip": skip,
        "limit": limit,
        "data": notifications
    }

@router.get("/users/{user_id}", response_model=PaginatedNotifications)
def get_all_user_notifs(
    user_id: int,
    skip: int = Query(0, ge=0, description="ile rekordow pominac"),
    limit: int = Query(10, ge=1, le=100, description="ile rekordow pobrac naraz"),
    db: Session = Depends(get_db)
):
    total = db.query(Notification).count()
    
    notifications = (
        db.query(Notification)
        .filter(Notification.user_id == user_id)
        .order_by(Notification.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    
    return {
        "total_records": total,
        "skip": skip,
        "limit": limit,
        "data": notifications
    }

@router.get("/{id}", response_model=NotificationResponse)
def get_notification_by_id(id: int, db: Session = Depends(get_db)):
    notification = db.query(Notification).filter(Notification.id == id).first()
    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"Powiadomienie z id {id} nie zostalo odnalezione"
        )
    return notification

@router.patch("/{id}/title", response_model=NotificationResponse)
def update_notification_title(id: int, payload: UpdateTitleRequest, db: Session = Depends(get_db)):
    notification = db.query(Notification).filter(Notification.id == id).first()
    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"Powiadomienie z id {id} nie zostalo odnalezione"
        )
        
    notification.title = payload.title
    db.commit()
    db.refresh(notification)
    return notification

@router.delete("/{id}", status_code=status.HTTP_200_OK)
def delete_notification(id: int, db: Session = Depends(get_db)):
    notification = db.query(Notification).filter(Notification.id == id).first()
    
    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"Powiadomienie z id {id} nie zostalo odnalezione"
        )

    db.delete(notification)
    db.commit()
    
    return {
        "status": "success",
        "message": f"Powiadomienie z id {id} zostalo usuniete"
    }