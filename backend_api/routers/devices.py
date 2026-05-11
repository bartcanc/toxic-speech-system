from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
from core import database
from models import tables
from models.tables import DevicePing

router = APIRouter(prefix="/api/devices", tags=["devices"])

@router.post("/ping")
def device_heartbeat(ping: DevicePing, db: Session = Depends(database.get_db)):
    
    device = db.query(tables.Device).filter(tables.Device.device_id == ping.device_id).first()
    
    # jezeli urzadzenie nie jest w bazie danych, dostaje odmowę
    if not device:
        raise HTTPException(
            status_code=403, 
            detail="Odmowa dostępu: Nierozpoznany identyfikator sprzętu."
        )

    device.last_seen = datetime.utcnow()
    device.status = ping.status
    db.commit()
    
    return {"message": "Sygnał odebrany", "device_id": ping.device_id}