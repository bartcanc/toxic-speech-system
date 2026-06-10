from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status, BackgroundTasks
from sqlalchemy.orm import Session
from datetime import datetime
from core import database
from models import tables
from schemas import ai_payloads
from zoneinfo import ZoneInfo
import os
import shutil
import requests

from core.database import get_db, SessionLocal
from models.tables import Notification, ToxicRecord

router = APIRouter(prefix="/api/devices", tags=["devices"])

AUDIO_DIR = "app/static/audio"
os.makedirs(AUDIO_DIR, exist_ok=True)

AI_SERVICE_URL = os.getenv("ai_research_URL")

@router.post("/ping")
def device_heartbeat(ping: ai_payloads.DevicePing, db: Session = Depends(database.get_db)):
    
    device = db.query(tables.Device).filter(tables.Device.device_id == ping.device_id).first()
    
    # jezeli urzadzenie nie jest w bazie danych, dostaje odmowę
    if not device:
        raise HTTPException(
            status_code=403, 
            detail="Odmowa dostępu: Nierozpoznany identyfikator sprzętu."
        )

    device.last_seen = datetime.now(ZoneInfo("Europe/Warsaw"))
    device.status = ping.status
    db.commit()
    
    return {"message": "Sygnał odebrany", "device_id": ping.device_id}

THRESHOLDS = {
    "TOXIC": 0.48,
    "SCAM": 0.09,
    "GROOMING": 0.35
}

def analyze_and_log_task(db_session_factory, transcription: str, db_audio_path: str, duration_seconds: int):
    db = db_session_factory()
    try:
        ai_response = requests.post(AI_SERVICE_URL, json={"text": transcription}, timeout=10)
        ai_response.raise_for_status()
        
        ai_data = ai_response.json() 
        ai_results = ai_data.get("results", {})
        scores = ai_results.get("confidence_scores", {})

        score_toxic = scores.get("toxic", 0.0)
        score_scam = scores.get("scam", 0.0)
        score_grooming = scores.get("grooming", 0.0)

        triggered_flag = None
        alert_label = "OK"
        category_code = 0

        if score_grooming >= THRESHOLDS["GROOMING"]:
            triggered_flag = "grooming"
            alert_label = "GROOMING"
            category_code = 3
        elif score_scam >= THRESHOLDS["SCAM"]:
            triggered_flag = "scam"
            alert_label = "SCAM"
            category_code = 2
        elif score_toxic >= THRESHOLDS["TOXIC"]:
            triggered_flag = "toxic"
            alert_label = "TOXIC"
            category_code = 1

        record = ToxicRecord(
            text_input=transcription,
            raw_ai_results=ai_data,
            triggered_flag=triggered_flag
        )
        db.add(record)
        
        db.flush()

        if triggered_flag is not None:
            alert = Notification(
                title=f"Wykryto zagrożenie: {alert_label}",
                device_name="SafeSound Device",
                transcription=transcription,
                audio_file_path=db_audio_path,
                audio_duration_seconds=duration_seconds,
                detected_category=category_code,
                toxic_record_id=record.id
            )
            db.add(alert)

        db.commit()
        print(f"[BACKGROUND TASK] Przetworzono tekst. Werdykt: {alert_label}")

    except Exception as e:
        db.rollback()
        print(f"[BACKGROUND TASK] Błąd krytyczny w tle: {str(e)}")
    finally:
        db.close()


@router.post("/upload", status_code=status.HTTP_202_ACCEPTED)
def receive_data_from_rpi(
    background_tasks: BackgroundTasks,
    audio_file: UploadFile = File(...),
    device_id: str = Form(...),
    transcription: str = Form(...),
    duration_seconds: int = Form(...),
    db: Session = Depends(get_db)
):
    try:
        timestamp = int(datetime.now(ZoneInfo("Europe/Warsaw")).timestamp())
        safe_filename = f"{device_id}_{timestamp}_{audio_file.filename}"
        file_path = os.path.join(AUDIO_DIR, safe_filename)
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(audio_file.file, buffer)
            
        db_audio_path = f"/static/audio/{safe_filename}"

        #   rozpoczynamy analize w tle, zeby nie blokowac RPI
        background_tasks.add_task(
            analyze_and_log_task, 
            SessionLocal, 
            transcription, 
            db_audio_path, 
            duration_seconds
        )

        return {
            "status": "accepted",
            "message": "Plik otrzymany. Rozpoczynam analize w tle",
            "device_id": device_id
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Nie mozna zaakceptowac payloadu: {str(e)}")
