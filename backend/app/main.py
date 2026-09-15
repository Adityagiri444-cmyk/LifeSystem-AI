from fastapi import FastAPI
from app.config import settings
from app.routers import health

app = FastAPI(
    title=settings.app_name,
    description="AI Personal Progression & Guidance System",
    version=settings.app_version,
)

app.include_router(health.router)

@app.get("/")
def home():
    return {
        "message": f"{settings.app_name} is running!",
        "status": "online",
        "environment": settings.environment,
    }