from storage.vectorStoreManager import VectorStoreManager
from storage.builder import LangChainDocumentBuilder
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_postgres.vectorstores import PGVector

import json, uuid, os, hashlib

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
chunk_dir = os.path.join(BASE_DIR, "chunk")


os.makedirs(chunk_dir, exist_ok=True)

# builder
builder = LangChainDocumentBuilder()

connection  = 'postgresql+psycopg://langchain:langchain@pgvector-container:5432/langchain'

embedding = HuggingFaceEmbeddings(
    model_name="BAAI/bge-base-en-v1.5",
    model_kwargs={"device": "cpu"},
    encode_kwargs={"normalize_embeddings": True}  # bge 권장 옵션
)

# DB connection
db = VectorStoreManager(connection, embedding, "rag_test")

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

    db.add_documents(docs)
    print(f"[INGESTED] {os.path.basename(json_path)} ({len(docs)} chunks)")

exts = ['/pdf']
chunk_json = []
for ext in exts:
    chunk_dir_ext = chunk_dir + ext + '/'
    for fname in os.listdir(chunk_dir_ext):
        if not fname.endswith('.json'):
            continue

        json_path = os.path.join(chunk_dir_ext + fname)
        ingest_chunk_file(json_path)
    




