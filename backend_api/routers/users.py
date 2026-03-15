from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from email_validator import validate_email, EmailNotValidError

import database
import auth
import schemas

router = APIRouter(prefix="/api/users", tags=["users"])

@router.post("/register", response_model=schemas.UserResponse)
def register_user(user: schemas.UserCreate, db: Session = Depends(database.get_db)):                #   depends to open database in case its not open already
    # try:
    #     validate_email(user.email)
    # except EmailNotValidError:
    #     raise HTTPException(status_code=400, detail="Niewłaściwy format adresu email")
    
    db_user = db.query(database.User).filter(database.User.email == user.email).first()             #   check user by email
    if db_user:
        raise HTTPException(status_code=400, detail="Ten email jest już zarejestrowany")            #   if user exists, return 400
    
    hashed_pwd = auth.get_password_hash(user.password)                                              #   else hash the password and save user in the db
    
    new_user = database.User(email=user.email, hashed_password=hashed_pwd)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return new_user

@router.post("/login", response_model=schemas.Token)
def login(user_credentials: schemas.UserLogin, db: Session = Depends(database.get_db)):             #   depends to open database in case its not open already
    # try:
    #     validate_email(user.email)
    # except EmailNotValidError:
    #     raise HTTPException(status_code=400, detail="Nieprawidłowy email lub hasło")

    user = db.query(database.User).filter(database.User.email == user_credentials.email).first()    #   check user by email
    
    if not user or not auth.verify_password(user_credentials.password, user.hashed_password):       #   if the user does not exist or an email/password was wrong 
        raise HTTPException(status_code=401, detail="Nieprawidłowy email lub hasło")                #   return 400
        
    access_token = auth.create_access_token(data={"sub": user.email})                               #   else generate token for the user and return said token
    return {"access_token": access_token, "token_type": "bearer"}