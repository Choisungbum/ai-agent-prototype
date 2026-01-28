from ingestion.storage.builder import LangChainDocumentBuilder
from ingestion.common.common import db_conn
import json, uuid, os, hashlib
import time

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
chunk_dir = os.path.join(BASE_DIR, "chunk")


os.makedirs(chunk_dir, exist_ok=True)

# builder
builder = LangChainDocumentBuilder()

# 임베딩하려는 document.page_content 또는 metadata 안에
# \x00 (NULL byte) 가 있으면 에러.
# PostgreSQL은 문자열에 0x00 절대 허용 안 함
def sanitize_text(s: str) -> str:
    if not s:
        return s
    return s.replace("\x00", "").replace("\x01", "").replace("\x02", "")

# chunk 데이터 조회
def load_chunks_from_json(chunk_path):
    with open(chunk_path, "r", encoding="utf-8") as f:
        return json.load(f)

#JSON → LangChain Document 변환
def build_documents_from_chunk_file(json_path):
    chunks = load_chunks_from_json(json_path)
    return LangChainDocumentBuilder.from_chunks(chunks)

# DB에 임베딩 + 저장
def ingest_chunk_file(json_path):
    docs = build_documents_from_chunk_file(json_path)
    if not docs:
        return
    
    for d in docs:
        d.page_content = sanitize_text(d.page_content)
        d.metadata = {
            k: sanitize_text(v) if isinstance(v, str) else v
            for k, v in d.metadata.items()
        }

    db.add_documents(docs)
    print(f"[INGESTED] {os.path.basename(json_path)} ({len(docs)} chunks)")

#  확장자별
exts = ['/pdf']
# 컬렉션 별 
collections = ['/wiseirag']
# 원문, 2단계 요약, 1단계 요약
chunk_json = ['/content', '/mid_summary', '/top_summary']

# 시작 시간
start = time.time()
print(f'### [embedding] start')
for ext in exts:
    for collection in collections:
        for chunk in chunk_json:
            db = db_conn(collection + chunk)
            chunk_dir_ext = chunk_dir + ext + collection + chunk
            for fname in os.listdir(chunk_dir_ext):
                if not fname.endswith('.json'):
                    continue

                json_path = os.path.join(chunk_dir_ext, fname)
                ingest_chunk_file(json_path)
                                                                                                                                                                                                                                                                                                                                                                  
print(f'### [embedding] end')
# 종료 시간  
end = time.time()
print(f'### [embedding] 총 걸린시간: {end-start}초')



