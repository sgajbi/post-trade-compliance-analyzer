# backend/core/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict
import os

class Settings(BaseSettings):
    """
    Application settings, loaded from environment variables or .env file.
    """
    model_config = SettingsConfigDict(env_file='.env', extra='ignore')

    APP_NAME: str = "Post-Trade Compliance Analyzer"
    CHROMA_DB_PATH: str = "./chroma_db"
    CHROMA_COLLECTION_NAME: str = "portfolio_collection"
    EMBEDDING_MODEL_NAME: str = "all-MiniLM-L6-v2"
    MONGO_DB_URL: str = "mongodb://localhost:27017/"
    MONGO_DB_NAME: str = "portfolio_analyzer_db"
    OPENAI_API_KEY: str # This should be set in your .env or environment variables

    # CORS settings - Consider making these more restrictive in production
    CORS_ALLOW_ORIGINS: list[str] = ["*"]
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: list[str] = ["*"]
    CORS_ALLOW_HEADERS: list[str] = ["*"]

# Create a settings instance to be imported across the application
settings = Settings()

# Optional: Print loaded settings (for debugging during development)
if os.getenv("ENV") == "development":
    print("Loaded Settings:")
    for key, value in settings.model_dump().items():
        print(f"  {key}: {value}")