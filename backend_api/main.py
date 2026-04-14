import os

if not os.path.exists("./backend_api/databases"):
    os.mkdir("./backend_api/databases")

from fastapi import FastAPI
from routers import users
from routers import analyze
from routers import admin

from core import database

database.Base.metadata.create_all(bind=database.engine)

app = FastAPI(title="Toxic Speech System API")

from core.database import SessionLocal
from models.tables import User
from core.auth import get_password_hash

def create_initial_admin():
    """tworzenie pierwszego admina, jesli baza jest pusta"""
    db = SessionLocal()
    try:
        admin_exists = db.query(User).filter(User.role == "admin").first()
        
        if not admin_exists:
            print("--> [SYSTEM] Brak konta administratora. Generowanie domyślnego admina...")
            admin_email = "admin@system.pl"
            admin_password = "admin"
            
            hashed_pwd = get_password_hash(admin_password)
            
            new_admin = User(
                email=admin_email, 
                hashed_password=hashed_pwd, 
                role="admin"
            )
            
            db.add(new_admin)
            db.commit()
            print(f"--> [SYSTEM] Konto admina utworzone pomyślnie! (Email: {admin_email})")
        else:
            print("--> [SYSTEM] Konto administratora już istnieje. Pomijam generowanie.")
    finally:
        db.close()

app.include_router(users.router)
app.include_router(analyze.router)
app.include_router(admin.router)

@app.on_event("startup")
async def startup_event():
    create_initial_admin()

@app.get("/")
def read_root():
    return {"status": "Server is running!"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)