from fastapi import FastAPI
from ingestion.routers import insgest, health

app = FastAPI()

app.include_router(ingestion.routers, preifx="/ingest", tags=["ingetst"])
app.include_router(ingestion.routers, prefix="/health")