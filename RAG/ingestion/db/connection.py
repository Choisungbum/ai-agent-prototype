from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

class connection():
    DATABASE_URL = "postgresql+psycopg2://wisenut:wisenut1!@my-postgres:5432/rag_db"

    engine = create_engine(DATABASE_URL, pool_pre_ping=True)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    Base = declarative_base()
