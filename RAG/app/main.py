from fastapi import FastAPI
from app.router.router import router

app = FastAPI(
    title="RAG Prototype"
)

app.include_router(router)