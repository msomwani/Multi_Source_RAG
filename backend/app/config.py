from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    POSTGRES_URL: str | None = None
    POSTGRES_URL_LOCAL: str | None = None
    CHROMA_DB_PATH: str = "./chroma_db"
    OPENAI_API_KEY: str
    EMBEDDING_MODEL: str = "text-embedding-3-small"
    APP_NAME: str = "Multi_Source_RAG"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()

DB_URL = settings.POSTGRES_URL or settings.POSTGRES_URL_LOCAL
