from functools import lru_cache
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    groq_api_key: Optional[str] = None
    groq_model: str = "qwen/qwen3-32b"
    ollama_model: str = "PetrosStav/gemma3-tools:4b"
    ollama_base_url: str = "http://localhost:11434"
    host: str = "0.0.0.0"
    port: int = 8000

    @property
    def use_groq(self) -> bool:
        return bool(self.groq_api_key)

    class Config:
        env_file = ".env"
        extra = "ignore"


@lru_cache()
def get_settings():
    return Settings()
