from fastapi import FastAPI
from app.routers.router import router as api_router

app = FastAPI()

app.include_router(api_router, prefix="/api", tags=["api"])

