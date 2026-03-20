from datetime import datetime, timedelta
from jose import JWTError, jwt
import bcrypt 
from fastapi.security import OAuth2PasswordBearer
from core.config import SECRET_KEY 

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7   # valid for a week
                            # M  * H  * D

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/users/login")

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
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
        
    to_encode.update({"exp": expire})
    
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt