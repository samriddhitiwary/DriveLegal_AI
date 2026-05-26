import os
from dotenv import load_dotenv
load_dotenv(override=True)

from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    google_api_key: str = os.getenv("GOOGLE_API_KEY", "")
    gemini_model: str = os.getenv("GEMINI_MODEL", "gemini-3.5-flash")
    chroma_db_dir: str = os.getenv("CHROMA_DB_DIR", "chroma_db")
    data_path: str = os.getenv("DATA_PATH", "app/data")
    embedding_model_name: str = os.getenv("EMBEDDING_MODEL_NAME", "sentence-transformers/all-MiniLM-L6-v2")
    memory_window_size: int = int(os.getenv("MEMORY_WINDOW_SIZE", "10"))

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
