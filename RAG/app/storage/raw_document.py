import json
from pathlib import Path
from datetime import datetime
from app.models.raw_document_model import RawDocumentModel

class RawDocumentStore:
    def __init__(self, base_dir: str = "data/raw"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def save_document(self, document: RawDocumentModel):
        """
        document raw_document 저장
        """
        path = self.base_dir / f"{document.doc_id}_document.json"
       
