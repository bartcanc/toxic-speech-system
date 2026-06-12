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
import asyncio

from core.database import get_db, SessionLocal
from models.tables import Notification, ToxicRecord, Device
from schemas.ai_payloads import AIResults, ConfidenceScores

router = APIRouter(prefix="/api/devices", tags=["devices"])

AUDIO_DIR = "/app/static/audio"
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

# TODO: jeszcze sprawdzic ta funkcje jak bedzie dostepny sprzet
def analyze_and_log_task(db_session_factory, transcription: str, db_audio_path: str, duration_seconds: int, device_id: str):
    with db_session_factory() as db:
        try:
            device = db.query(Device).filter(Device.device_id == device_id).first()
            owner_id = device.owner_id if device else None
            
            # odczytanie wynikow analizy ai
            ai_response = requests.post(AI_SERVICE_URL, json={"text": transcription}, timeout=10)
            ai_response.raise_for_status()
            # ---------------------------------

            # mock na potrzeby testów bez sprzętu
            # ai_response = AIResults(
            #     is_safe=True, 
            #     detected_flags={'OK'}, 
            #     confidence_scores=ConfidenceScores(toxic=0.0, scam=0.0, grooming=0.0)
            # )
            # print(ai_response)
            
            ai_data = ai_response.model_dump() 
            scores = ai_data.get("confidence_scores", {})

            score_toxic = scores.get("toxic", 0.0)
            score_scam = scores.get("scam", 0.0)
            score_grooming = scores.get("grooming", 0.0)

            # TODO: zamienic triggered flag na liste (do ustalenia)
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
                triggered_flag=triggered_flag,
                owner_id=owner_id
            )
            db.add(record)
            
            db.flush()

            if triggered_flag is not None:
                alert = Notification(
                    user_id=owner_id,
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
            print(f"[BACKGROUND TASK] Przetworzono tekst. Werdykt: {alert_label}", flush=True)

        except Exception as e:
            db.rollback()
            print(f"[BACKGROUND TASK] Błąd krytyczny w tle: {str(e)}")


@router.post("/upload", status_code=status.HTTP_202_ACCEPTED)
async def receive_data_from_rpi(
    audio_file: UploadFile = File(...),
    device_id: str = Form(...),
    transcription: str = Form(...),
    duration_seconds: int = Form(...)
):
    #   TODO: add some sort of validation for file format
    try:
        timestamp = int(datetime.now(ZoneInfo("Europe/Warsaw")).timestamp())
        safe_filename = f"{device_id}_{timestamp}_{audio_file.filename}"
        file_path = os.path.join(AUDIO_DIR, safe_filename)
        
        content = await audio_file.read()
        with open(file_path, "wb") as buffer:
            buffer.write(content)
        db_audio_path = f"/static/audio/{safe_filename}"

        #   rozpoczynamy analize w tle, zeby nie blokowac RPI
        loop = asyncio.get_running_loop()
        loop.run_in_executor(
            None,
            analyze_and_log_task, 
            SessionLocal, 
            transcription, 
            db_audio_path, 
            duration_seconds,
            device_id
        )

        return {
            "status": "accepted",
            "message": "Plik otrzymany. Rozpoczynam analize w tle",
            "device_id": device_id
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Nie mozna zaakceptowac payloadu: {str(e)}")
