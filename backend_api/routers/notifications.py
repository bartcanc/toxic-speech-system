from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional

from core.database import get_db
from models.tables import Notification, User
from schemas.notif_schemas import NotificationResponse, UpdateTitleRequest, NotificationCreate, PaginatedNotifications

from core.auth import get_current_admin, get_current_user

router = APIRouter(
    prefix="/api/notifications",
    tags=["Notifications"]
)

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
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """
        Endpoint dla admina
    """
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

@router.get("/my_notifs", response_model=PaginatedNotifications)
def get_all_user_notifs(
    skip: int = Query(0, ge=0, description="ile rekordow pominac"),
    limit: int = Query(10, ge=1, le=100, description="ile rekordow pobrac naraz"),
    search_title: Optional[str] = Query(None, description="szukanie fragmentu tekstu w tytule powiadomienia"),
    is_read: Optional[bool] = Query(None, description="filtrowanie false - nieodczytane, true - odczytane"),
    sort_date: str = Query("desc", regex="^(asc|desc)$", description="sortowanie po dacie, asc/desc"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Notification).filter(Notification.user_id == current_user.id)
    
    if search_title:
        query = query.filter(Notification.title.ilike(f"%{search_title}%"))
    if is_read is not None:
        query = query.filter(Notification.is_read == is_read)

    total = query.count()

    if sort_date == "asc":
        query = query.order_by(Notification.created_at.asc())
    else:
        query = query.order_by(Notification.created_at.desc())

    notifications = query.offset(skip).limit(limit).all()

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
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
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
def get_notification_by_id(
        id: int, 
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
    ):
    notification = db.query(Notification).filter(Notification.id == id, Notification.user_id == current_user.id).first()
    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"Powiadomienie z id {id} nie zostalo odnalezione"
        )
    return notification

@router.patch("/{id}/title", response_model=NotificationResponse)
def update_notification_title(
        id: int, 
        payload: UpdateTitleRequest, 
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
    ):
    notification = db.query(Notification).filter(Notification.id == id, Notification.user_id == current_user.id).first()
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
def delete_notification(
        id: int, 
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
    ):
    notification = db.query(Notification).filter(Notification.id == id, Notification.user_id == current_user.id).first()
    
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