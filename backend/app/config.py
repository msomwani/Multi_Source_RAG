import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    POSTGRES_URL:str
    CHROMA_DB_PATH:str="./chroma_db"
    OPENAI_API_KEY:str
    EMBEDDING_MODEL:str="text-embedding-3-small"
    APP_NAME:str="Multi_SOurce_RAG"

    class Config:
        env_file="app/.env"
        env_file_encoding="utf-8"

settings=Settings()