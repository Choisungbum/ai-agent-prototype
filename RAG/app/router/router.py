from fastapi import APIRouter
from app.services import ingestService

router = APIRouter(
    prefix="/api",
    tags=["api"]
)

ingest_service = ingestService

@router.get("/health")
def health_check():
    return {"status": "ok"}

@router.post("/load")
def document_load(source_dir: str):
    return ingest_service.ingest(source_dir)