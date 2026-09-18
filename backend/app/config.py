from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    app_name: str = "LifeSystem"
    app_version: str = "1.0.0"
    environment: str = "development"
    debug: bool = True
    database_url: str = "postgresql://postgres:password@localhost:5432/lifesystem_dev"
    secret_key: str = "change-this-to-a-random-secret-in-env"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    class Config:
        env_file = ".env"


settings = Settings()