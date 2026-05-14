from sqlalchemy import create_engine, Column, Integer, String, Boolean, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship, sessionmaker, Session
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

from core.database import Base

class User(Base):                                               #   user database
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)          #   id
    username = Column(String, default=f"new_user_{id}")         #   username
    email = Column(String, unique=True, index=True)             #   user email
    hashed_password = Column(String)                            #   user password
    role = Column(String, default="user")                       #   user role (admin/moderator/user)
    created = Column(DateTime)                                  #   user creation date

    reset_code = Column(String, nullable=True)
    reset_code_expire = Column(DateTime, nullable=True)
    
    devices = relationship("Device", back_populates="owner")

class Device(Base):                                                     # registered devices
    __tablename__ = "devices"
    
    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(String, unique=True, index=True, nullable=False) # fabryczne ID
    last_seen = Column(DateTime, nullable=True)
    status = Column(String, default="inactive")                         # inactive, active, error
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=True) 
    owner = relationship("User")

# class ToxicRecord(Base):                                        #   toxicity records    (TBD)
#     __tablename__ = "toxic_records"
#     #   TO BE DETERMINED