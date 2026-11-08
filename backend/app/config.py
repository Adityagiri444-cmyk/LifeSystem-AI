from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "LifeSystem"
    app_version: str = "1.0.0"
    environment: str = "development"
    debug: bool = True
    database_url: str = "postgresql://postgres:password@localhost:5432/lifesystem_dev"
    secret_key: str = "change-this-to-a-random-secret-in-env"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    # Optional LLM (any OpenAI-compatible chat API). Leave blank to use templates only.
    llm_base_url: str = ""
    llm_api_key: str = ""
    llm_model: str = ""
    llm_timeout_seconds: float = 10.0


settings = Settings()