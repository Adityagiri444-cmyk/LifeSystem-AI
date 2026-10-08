from fastapi import FastAPI
from app.config import settings
from app.routers import health, quests, auth, profile, goals, assessment, status, roadmap, insights
from app.database import Base, engine
from app import models

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
app.include_router(status.router)
app.include_router(roadmap.router)
app.include_router(insights.router)

Base.metadata.create_all(bind=engine)

@app.get("/")
def home():
    return {
        "message": f"{settings.app_name} is running!",
        "status": "online",
        "environment": settings.environment,
    }