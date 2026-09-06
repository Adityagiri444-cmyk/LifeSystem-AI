from fastapi import FastAPI

app = FastAPI(
    title="LifeSystem",
    description="AI Personal Progression & Guidance System",
    version="1.0.0"
)


@app.get("/")
def home():
    return {
        "message": "LifeSystem is running!",
        "status": "online"
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy"
    }