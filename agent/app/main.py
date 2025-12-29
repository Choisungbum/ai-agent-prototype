from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.routers import chat_router

app = FastAPI(title="langChain Test")

# 🔹 chat_router를 등록 ("/chat" 엔드포인트 포함)
app.include_router(chat_router.router)
# app.include_router(chat_langfuse_router.router)

