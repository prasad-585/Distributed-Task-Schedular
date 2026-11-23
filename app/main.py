from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.database import create_db_and_tables
from app.routers import auth, tasks

@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield

app = FastAPI(
    title="Distributed Task Scheduling Engine",
    description="Learning portfolio project: FastAPI + PostgreSQL + Redis + Scheduler + Worker",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(auth.router)
app.include_router(tasks.router)

@app.get("/", tags=["Health"])
def home():
    return {"message": "Distributed Task Scheduler API is running"}

@app.get("/health", tags=["Health"])
def health():
    return {"status": "healthy"}
