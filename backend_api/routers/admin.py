from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from core import database

from core.auth import get_current_admin 
from models import tables
from schemas import auth_schemas

router = APIRouter(
    prefix="/api/admin",
    tags=["admin panel"],
    dependencies=[Depends(get_current_admin)]
)

@router.get("/users", response_model=List[auth_schemas.UserProfile])
def get_all_users(db: Session = Depends(database.get_db)):
    """Zwraca listę wszystkich użytkowników w systemie (bez haseł)."""
    users = db.query(tables.User).all()
    return users

@router.patch("/users/{user_id}/role", response_model=auth_schemas.UserProfile)
def update_user_role(
    user_id: int, 
    role_data: auth_schemas.RoleUpdate, 
    db: Session = Depends(database.get_db)
):
    """Zmienia rolę wybranego użytkownika (np. z 'user' na 'moderator' lub 'admin')."""
    user = db.query(tables.User).filter(tables.User.id == user_id).first()
    
    if not user:
        raise HTTPException(status_code=404, detail="Użytkownik nie znaleziony")
    
    allowed_roles = ["user", "moderator", "admin"]
    if role_data.new_role not in allowed_roles:
        raise HTTPException(status_code=400, detail="Nieprawidłowa rola")

    user.role = role_data.new_role
    db.commit()
    db.refresh(user)
    
    return user

@router.delete("/users/{user_id}")
def delete_user(
    user_id: int, 
    current_admin: tables.User = Depends(get_current_admin),
    db: Session = Depends(database.get_db)
):
    """Trwale usuwa użytkownika z bazy danych."""
    
    if current_admin.id == user_id:
        raise HTTPException(
            status_code=400, 
            detail="Operacja niedozwolona: Nie możesz usunąć własnego konta!"
        )

    user = db.query(tables.User).filter(tables.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Użytkownik nie znaleziony")

    db.delete(user)
    db.commit()
    
    return {"message": f"Użytkownik {user.email} został pomyślnie usunięty."}