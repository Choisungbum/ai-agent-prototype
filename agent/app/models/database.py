import os
import redis.asyncio as redis
from dotenv import load_dotenv

load_dotenv()

# 전역 Redis 클라이언트 (초기엔 None)
redis_client = None

async def init_redis():
    global redis_client
    redis_client = redis.from_url(
        os.getenv("REDIS_URL"), 
        decode_responses=True
    )

async def close_redis():
    global redis_client
    if redis_client:
        await redis_client.close()