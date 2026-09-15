from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    app_name: str = "LifeSystem"
    app_version: str = "1.0.0"
    environment: str = "development"
    debug: bool = True

    class Config:
        env_file = ".env"

settings = Settings()