
import os
from functools import lru_cache
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    google_api_key: str
    host: str = "0.0.0.0"
    port: int = 8000
    
    class Config:
        env_file = ".env"

@lru_cache()
def get_settings():
    return Settings()

