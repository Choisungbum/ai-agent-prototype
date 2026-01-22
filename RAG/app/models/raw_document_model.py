from datetime import datetime
from uuid import UUID
from pydantic import BaseModel
from typing import Any, List


# ===== raw_documents =====

class RawDocumentModel(BaseModel):
    doc_id: UUID
    source: str
    file_type: str
    content: Any  # JSONB
    created_at: datetime


# ===== raw_tables =====

class RawTableModel(BaseModel):
    table_id: str
    doc_id: UUID
    page: int
    rows: List[List[str]]  # JSONB
    created_at: datetime
