import chromadb
from app.config import settings


client=chromadb.PersistentClient(path=settings.CHROMA_DB_PATH)