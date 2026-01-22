from langchain_postgres.vectorstores import PGVector
from langchain_core.documents import Document

class VectorStoreManager:
    def __init__(self, connection, embedding, collection_name):
        self.db = PGVector(
            connection=connection,
            embeddings=embedding,
            collection_name=collection_name
        )

    def add_documents(self, docs):
        self.db.add_documents(docs)

    def get_retriever(self, k=5):
        return self.db.as_retriever(search_kwargs={"k": k})