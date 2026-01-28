from ingestion.storage.vectorStoreManager import VectorStoreManager

from langchain_huggingface import HuggingFaceEmbeddings
from langchain_postgres.vectorstores import PGVector

connection  = 'postgresql+psycopg://langchain:langchain@pgvector-container:5432/langchain'

embedding = HuggingFaceEmbeddings(
    model_name="BAAI/bge-base-en-v1.5",
    model_kwargs={"device": "cpu"},
    encode_kwargs={"normalize_embeddings": True}  # bge 권장 옵션
)

def db_conn(collection_name:str) -> VectorStoreManager:
    # DB connection
    return VectorStoreManager(connection
                              , embedding
                              , collection_name)