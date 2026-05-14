from datetime import datetime, timedelta
from jose import JWTError, jwt
import bcrypt 
from fastapi.security import OAuth2PasswordBearer
from core.config import SECRET_KEY
import string, random

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
from core import database
from models import tables
from zoneinfo import ZoneInfo

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7   # valid for a week
                            # M  * H  * D

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/users/login")

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(database.get_db)):
    """Rozpakowuje token i szuka użytkownika w bazie."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Nie można zweryfikować tokena",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub") 
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = db.query(tables.User).filter(tables.User.email == email).first()
    if user is None:
        raise credentials_exception
        
    return user

def get_current_admin(current_user: tables.User = Depends(get_current_user)):
    """Wpuszcza tylko użytkowników, którzy mają wpisane 'admin' w kolumnie role."""
    if getattr(current_user, "role", "user") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Brak wystarczających uprawnień (Wymagany Admin)."
        )
    return current_user

"""
verify_password - compares the input password with a hashed password in the database using bytes

!!! ONLY ON LOGIN   !!!
"""
def verify_password(plain_password: str, hashed_password: str) -> bool:
    password_bytes = plain_password.encode('utf-8')
    hash_bytes = hashed_password.encode('utf-8')
    return bcrypt.checkpw(password_bytes, hash_bytes)

"""
get_password_hash - converts input password to hashed password that can be saved in the database

!!! ONLY DURING USER CREATION   !!!
"""
def get_password_hash(password: str) -> str:
    pwd_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(pwd_bytes, salt)
    return hashed_password.decode('utf-8')

"""
create_access_token - creates a token for a set period of time for a user to be able to use the services

!!! ONLY ON LOGIN   !!!
"""
def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.now(ZoneInfo("Europe/Warsaw")) + expires_delta
    else:
        expire = datetime.now(ZoneInfo("Europe/Warsaw")) + timedelta(minutes=15)
        
    to_encode.update({"exp": expire})
    
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt