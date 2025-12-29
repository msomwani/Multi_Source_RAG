from fastapi import FastAPI
from app.api import routes_ingest, routes_query

app = FastAPI()

app.include_router(routes_ingest.router)
app.include_router(routes_query.router)

@app.get("/health")
def health():
    return {"status": "ok"}
