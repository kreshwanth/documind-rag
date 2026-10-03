from typing import List, Union
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
import json
import os

class Settings(BaseSettings):
    PROJECT_NAME: str = "DocuMind"
    ENVIRONMENT: str = "development"

    # Database
    DATABASE_URL: str = "postgresql://documind_user:documind_secure_password@localhost:5432/documind_db"

    # Security & JWT
    JWT_SECRET: str = "documind_super_secret_jwt_key_change_in_production_987234982374"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours

    # Google Gemini AI
    GEMINI_API_KEY: str = ""
    EMBEDDING_MODEL: str = "text-embedding-004"
    LLM_MODEL: str = "gemini-1.5-flash"
    EMBEDDING_DIMENSION: int = 768

    # RAG Retrieval Hyperparameters
    TOP_K: int = 8
    SIMILARITY_THRESHOLD: float = 0.15

    # Document Ingestion & Storage
    UPLOAD_DIRECTORY: str = "./uploads"
    MAX_FILE_SIZE_MB: int = 50
    CHUNK_SIZE: int = 600
    CHUNK_OVERLAP: int = 100

    # CORS Allowed Origins
    BACKEND_CORS_ORIGINS: Union[List[str], str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
    ]

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, str) and v.startswith("["):
            return json.loads(v)
        return v

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()

# Ensure upload directory exists
os.makedirs(settings.UPLOAD_DIRECTORY, exist_ok=True)
