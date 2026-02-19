from fastapi import APIRouter
from pydantic import BaseModel

import os, time

router = APIRouter()
print("router imported")
@router.post("/")
def api():
    # TODO: 기존 ingestion 로직 호출
    return {"status": "ok"}


# ── Request / Response ──────────────────────────────

class RetrieveRequest(BaseModel):
    query: str

class RetrieveResponse(BaseModel):
    query: str
    response: str
    sources: list[dict]
    elapsed_sec: float


# ── 1. 전처리 ───────────────────────────────────────
 # 작엄 문서 작업할 디렉토리로 copy
 # raw
 # ↓ (copy)
 # staging
 # ↓ (Hancom Office COM 자동화, ahk)
 # converted
 # ↓
 # PDF loader
 # convert_docs_in_dir(raw_dir, staging_dir, converted_dir)
@router.get("/preprocessing")
def preprocessing():
    from app.loaders.libreoffice import convert_docs_in_dir
    from app.service.preprocessing import ( chunk_file, get_ext, raw_dir, staging_dir, converted_dir, )

    print('preprocessing 시작')
    start = time.time()

    # 문서 변환 (raw → staging → converted)
    convert_docs_in_dir(raw_dir, staging_dir, converted_dir)

    # 변환된 PDF 청킹
    processed = []
    for name in os.listdir(converted_dir):
        if get_ext(name) not in ['.pdf']:
            continue
        chunk_file(os.path.join(converted_dir, name))
        processed.append(name)

    elapsed = round(time.time() - start, 2)
    print('preprocessing 종료')
    return {
        "status": "ok",
        "processed_files": processed,
        "elapsed_sec": elapsed,
    }


# ── 2. 임베딩 ───────────────────────────────────────

@router.get("/embedding")
def embedding():
    from app.service.embedding import run_embedding

    print('embedding 시작')
    result = run_embedding()
    print('embedding 종료')
    return {"status": "ok", **result}


# ── 3. 검색 + LLM 응답 ─────────────────────────────

@router.post("/retrieve", response_model=RetrieveResponse)
async def retrieve(req: RetrieveRequest):
    from app.service.retriever import ( retrieve_pipeline, build_context)
    from app.common.LLMClient import call_llm
    print('retrieve 시작')
    start = time.time()

    # 검색
    raw_results = retrieve_pipeline(req.query)
    sources, context = build_context(raw_results)

    # LLM 응답 생성
    raw_response = await call_llm(req.query, context)
    response = raw_response['choices'][0]['message']['content']

    elapsed = round(time.time() - start, 2)
    print('retrieve 종료')
    return RetrieveResponse(
        query=req.query,
        response=response,
        sources=sources,
        elapsed_sec=elapsed,
    )
