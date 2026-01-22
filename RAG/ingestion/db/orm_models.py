import uuid
from sqlalchemy import Column, String, JSON, ForeignKey
from sqlalchemy.orm import relationship
from db.connection import Connection

Base = Connection.Base


class Document(Base):
    __tablename__ = "documents"

    doc_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    source = Column(String, nullable=False)
    file_type = Column(String, nullable=False)
    content = Column(JSON, nullable=True)

    blocks = relationship(
        "Block",
        back_populates="document",
        cascade="all, delete-orphan"
    )


class Block(Base):
    __tablename__ = "blocks"

    block_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    section_id = Column(String, nullable=False)
    doc_id = Column(String, ForeignKey("documents.doc_id"), nullable=False)

    page = Column(String, nullable=True)
    block_index = Column(String, nullable=True)
    block_type = Column(String, nullable=False)   # text | table | image
    text = Column(JSON, nullable=False)

    document = relationship("Document", back_populates="blocks")
