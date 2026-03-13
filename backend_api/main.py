from fastapi import FastAPI
from routers import users

import database

database.Base.metadata.create_all(bind=database.engine)

app = FastAPI(title="Toxic Speech System API")

app.include_router(users.router)

@app.get("/")
def read_root():
    return {"status": "Server is running!"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)