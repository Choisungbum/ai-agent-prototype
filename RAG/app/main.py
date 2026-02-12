from fastapi import FastAPI
from app.routers.router import router as api_router
from app.routers.ingest import router as ingest_router

app = FastAPI()

app.include_router(api_router)
app.include_router(ingest_router, prefix="/ingest", tags=["ingest"])
