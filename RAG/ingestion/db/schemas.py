from pydantic import BaseModel
from typing import List, Dict, Any, Optional


class BlockCreate(BaseModel):
    block_id: str
    doc_id: str
    section_id: str
    page: Optional[int]
    block_index: Optional[int]
    block_type: str
    text: str


class DocumentCreate(BaseModel):
    doc_id: str
    source: str
    file_type: str
    content: Any
