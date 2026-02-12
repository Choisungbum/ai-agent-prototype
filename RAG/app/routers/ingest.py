# ingestion/routers/ingest.py
from fastapi import APIRouter

router = APIRouter()

@router.post("/")
def ingest():
    # TODO: 기존 ingestion 로직 호출
    return {"status": "ok"}
