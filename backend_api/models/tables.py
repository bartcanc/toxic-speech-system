from sqlalchemy import create_engine, Column, Integer, String, Boolean, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship, sessionmaker, Session
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

from core.database import Base

class User(Base):                                               #   user database
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)          #   id
    email = Column(String, unique=True, index=True)             #   user email
    hashed_password = Column(String)                            #   user password
    
    devices = relationship("Device", back_populates="owner")

class Device(Base):                                             #   registered devices
    __tablename__ = "devices"

    id = Column(Integer, primary_key=True, index=True)          #   id
    device_id = Column(String, unique=True, index=True)         #   unique device id
    name = Column(String)                                       #   device name
    
    owner_id = Column(Integer, ForeignKey("users.id"))          #   owner id
    
    owner = relationship("User", back_populates="devices")
    #records = relationship("ToxicRecord", back_populates="device")

# class ToxicRecord(Base):                                        #   toxicity records    (TBD)
#     __tablename__ = "toxic_records"
#     #   TO BE DETERMINED