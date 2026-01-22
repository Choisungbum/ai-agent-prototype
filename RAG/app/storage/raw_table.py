import json
from pathlib import Path
from datetime import datetime
from app.models.raw_document_model import RawTableModel

class RawDocumentStore:
    def __init__(self, base_dir: str = "data/raw"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def save_table(self, table: RawTableModel):
        """
        table raw_table 저장
        """
        path = self.base_dir / f"{table.doc_id}_table.json"
        
