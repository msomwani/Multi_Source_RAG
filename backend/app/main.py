from fastapi import FastAPI
from app.api import routes_ingest, routes_query,routes_conversations

app = FastAPI()

from fastapi.middleware.cors import CORSMiddleware

#allows requests form this endpoints
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5173", "http://localhost:5173","http://localhost:3000",
        "http://127.0.0.1:3000",],
    allow_credentials=True,
    allow_methods=["*"],   # REQUIRED so OPTIONS works
    allow_headers=["*"],   # REQUIRED
)

app.include_router(routes_ingest.router)
app.include_router(routes_query.router)
app.include_router(routes_conversations.router)

@app.get("/health")
def health():
    return {"status": "ok"}
