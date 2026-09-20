from fastapi import FastAPI
from app.config import settings
from app.routers import health, quests, auth
from app.database import Base, engine
from app import models
from app.routers import health, quests, auth, profile
from app.routers import health, quests, auth, profile, goals
from app.routers import health, quests, auth, profile, goals, assessment

app = FastAPI(
    title=settings.app_name,
    description="AI Personal Progression & Guidance System",
    version=settings.app_version,
)

app.include_router(health.router)
app.include_router(quests.router)
app.include_router(auth.router)
app.include_router(profile.router)
app.include_router(goals.router)
app.include_router(assessment.router)
Base.metadata.create_all(bind=engine)

@app.get("/")
def home():
    return {
        "message": f"{settings.app_name} is running!",
        "status": "online",
        "environment": settings.environment,
    }