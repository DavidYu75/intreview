from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    APP_NAME: str = "Intreview"
    MONGODB_URL: str = "mongodb://localhost:27017"
    DATABASE_NAME: str = "intreview_db"
    JWT_SECRET_KEY: str = "your-secret-key"  # Change this in production
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    class Config:
        env_file = ".env"

@lru_cache()
def get_settings():
    return Settings()