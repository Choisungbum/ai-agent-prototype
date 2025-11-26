from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.routers import chat_router
from app.models.database import init_redis, close_redis

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_redis()  # Redis 연결
    print("✅ Redis Connected")
    yield
    await close_redis() # Redis 해제
    print("❌ Redis Closed")

app = FastAPI(title="langChain Test", lifespan=lifespan)

# 🔹 chat_router를 등록 ("/chat" 엔드포인트 포함)
app.include_router(chat_router.router)
# app.include_router(chat_langfuse_router.router)

