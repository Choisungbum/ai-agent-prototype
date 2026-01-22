from sqlalchemy.orm import Session
# from ingestion.db.schemas import BlockCreate, DocumentCreate
from ingestion.db.orm_models import RawBlocksModel

class RawDocumentRepository:
    def insert(self, db: Session, document: RawDocumentModel):
        db.add(document)
        db.commit()

    def get(self, db: Session, doc_id):
        return db.query(RawDocumentModel).filter(RawDocumentModel.doc_id == doc_id).first()
    

class RawBlocksRepository:
    def insert(self, db: Session, document: RawBlocksModel):
        db.add(document)
        db.commit()

    def get(self, db: Session, doc_id):
        return db.query(RawBlocksModel).filter(RawBlocksModel.doc_id == doc_id).first()