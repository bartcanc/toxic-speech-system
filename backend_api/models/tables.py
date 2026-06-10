from sqlalchemy import create_engine, Column, Integer, String, Boolean, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship, sessionmaker, Session
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
from zoneinfo import ZoneInfo
from sqlalchemy.dialects.postgresql import JSONB

from core.database import Base

class User(Base):                                               #   user database
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)          #   id
    username = Column(String, default=f"new_user_{id}")         #   username
    email = Column(String, unique=True, index=True)             #   user email
    hashed_password = Column(String)                            #   user password
    role = Column(String, default="user")                       #   user role (admin/moderator/user)
    created = Column(DateTime)                                  #   user creation date
    is_premium = Column(Boolean, default=False)                 #   users premium status

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

class Notification(Base):                                               #   user notifications
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)                                                      #   id
    toxic_record_id = Column(Integer, ForeignKey("toxic_records.id", ondelete="SET NULL"), nullable=True)   #   id rekordu toxicrecord
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True)                    #   id uzytkownika, do ktorego wyslane jest powiadomienie
    title = Column(String(255), nullable=False, default="Nowe powiadomienie")                               #   nazwa powiadomienia
    device_name = Column(String(100), nullable=False, default="SafeSound 1st Edition")                      #   nazwa urzadzenia ktore wyslalo powiadomienie
    transcription = Column(Text, nullable=False)                                                            #   transkrypcja audio
    audio_file_path = Column(String(500), nullable=True)                                                    #   sciezka do pliku audio na serwerze
    audio_duration_seconds = Column(Integer, default=0)                                                     #   czas trwania nagrania w sekundach
    created_at = Column(DateTime, default=lambda: datetime.now(ZoneInfo("Europe/Warsaw")))                          #   data utworzenia rekordu
    is_read = Column(Boolean, default=False)                                                                #   czy powiadomienie zostalo odczytane
    detected_category = Column(Integer, default=0)

    user = relationship("User", backref="notifications")
    toxic_record = relationship("ToxicRecord", backref="notification")
    # device = relationship("Device", backref="notifications")

class ToxicRecord(Base):                                        #   toxicity records    (TBD)
    __tablename__ = "toxic_records"

    id = Column(Integer, primary_key=True, index=True)                                      #   id
    text_input = Column(Text, nullable=False)                                               #   transkrypcja audio do analizy
    raw_ai_results = Column(JSONB, nullable=False)                                          #   surowe dane po analizie przez AI
    triggered_flag = Column(String(50), nullable=True)                                      #   co wykrylo ai (label)
    created_at = Column(DateTime, default=lambda: datetime.now(ZoneInfo("Europe/Warsaw")))          #   czas stworzenia rekordu