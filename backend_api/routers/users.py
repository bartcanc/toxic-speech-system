from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from email_validator import validate_email, EmailNotValidError
from fastapi.security import OAuth2PasswordRequestForm
from core import database
from core import auth
from schemas import auth_schemas
from models import tables
from core.auth import get_current_admin, get_current_user
import random
import string
from datetime import datetime, timedelta
from core.auth import get_password_hash
from services.email_service import send_reset_email
from zoneinfo import ZoneInfo

router = APIRouter(prefix="/api/users", tags=["users"])

def generate_otp_code(length=6):
    characters = string.ascii_uppercase + string.digits
    return ''.join(random.choice(characters) for _ in range(length))


@router.post("/register", response_model=auth_schemas.UserResponse)
def register_user(user: auth_schemas.UserCreate, db: Session = Depends(database.get_db)):                #   depends to open database in case its not open already
    try:
        validate_email(user.email)
    except EmailNotValidError:
        raise HTTPException(status_code=400, detail="Niewłaściwy format adresu email")
    
    db_user = db.query(tables.User).filter(tables.User.email == user.email).first()             #   check user by email
    if db_user:
        raise HTTPException(status_code=400, detail="Ten email jest już zarejestrowany")            #   if user exists, return 400
    
    hashed_pwd = auth.get_password_hash(user.password)                                              #   else hash the password and save user in the db
    
    new_user = tables.User(username=user.username,email=user.email, hashed_password=hashed_pwd, created=datetime.now(ZoneInfo("Europe/Warsaw")))
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return new_user

@router.post("/login", response_model=auth_schemas.Token)
def login(user_credentials: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(database.get_db)):             #   depends to open database in case its not open already
    try:
        validate_email(user_credentials.username)
    except EmailNotValidError:
        raise HTTPException(status_code=400, detail="Nieprawidłowy email lub hasło")

    user = db.query(tables.User).filter(tables.User.email == user_credentials.username).first()    #   check user by email
    
    if not user or not auth.verify_password(user_credentials.password, user.hashed_password):       #   if the user does not exist or an email/password was wrong 
        raise HTTPException(status_code=401, detail="Nieprawidłowy email lub hasło")                #   return 400
        
    access_token = auth.create_access_token(data={"sub": user.email})                               #   else generate token for the user and return said token
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/admin-only")
def get_admin_data(current_admin: tables.User = Depends(get_current_admin)):
    return {"message": f"Witaj w tajnym panelu, szefie! Twój email to: {current_admin.email}"}

@router.get("/me")
def get_my_profile(current_user: tables.User = Depends(get_current_user)):
    """
    Prywatny profil użytkownika. 
    Wymaga podania ważnego tokena (nagłówek Authorization).
    """
    return {
        "message": "Witaj w strefie dla zalogowanych!",
        "twoja_nazwa": current_user.username,
        "twoj_email": current_user.email,
        "twoja_rola": current_user.role,
        "twoje_id": current_user.id,
        "data utworzenia konta": current_user.created.strftime("%x")
    }


@router.post("/forgot-password")
def request_password_reset(
    req: auth_schemas.PasswordResetRequest, 
    background_tasks: BackgroundTasks,
    db: Session = Depends(database.get_db)
):
    user = db.query(tables.User).filter(tables.User.email == req.email).first()
    
    if user:
        code = generate_otp_code()
        user.reset_code = code
        user.reset_code_expire = datetime.now(ZoneInfo("Europe/Warsaw")) + timedelta(minutes=15)
        db.commit()
        
        background_tasks.add_task(send_reset_email, user.email, code)

    return {"message": "Jeśli podany adres e-mail istnieje w naszej bazie, wysłano na niego kod weryfikacyjny."}

@router.post("/reset-password")
def confirm_password_reset(
    req: auth_schemas.PasswordResetConfirm, 
    db: Session = Depends(database.get_db)
):
    user = db.query(tables.User).filter(tables.User.email == req.email).first()
    
    if not user or user.reset_code != req.reset_code:
        raise HTTPException(status_code=400, detail="Nieprawidłowy e-mail lub kod weryfikacyjny.")
        
    if not user.reset_code_expire or datetime.now(ZoneInfo("Europe/Warsaw")) > user.reset_code_expire:
        raise HTTPException(status_code=400, detail="Kod weryfikacyjny wygasł. Wygeneruj nowy.")

    user.hashed_password = get_password_hash(req.new_password)
    
    user.reset_code = None
    user.reset_code_expire = None
    
    db.commit()
    
    return {"message": "Twoje hasło zostało pomyślnie zmienione. Możesz się teraz zalogować."}

@router.post("/change-password")
def change_password(
    req: auth_schemas.PasswordChange,
    current_user: tables.User = Depends(get_current_user), # <--- WYMAGA TOKENA
    db: Session = Depends(database.get_db)
):
    """
    Zmiana hasła dla zalogowanego użytkownika.
    Wymaga podania obecnego hasła dla potwierdzenia tożsamości.
    """
    if not auth.verify_password(req.old_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Obecne hasło jest nieprawidłowe."
        )
    
    current_user.hashed_password = auth.get_password_hash(req.new_password)
    db.commit()
    
    return {"message": "Hasło zostało pomyślnie zmienione."}