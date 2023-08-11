from sqlalchemy import (
    MetaData,
    create_engine,
)
from sqlalchemy.orm import sessionmaker

from src.constants import DB_NAMING_CONVENTION

DATABASE_URL = "sqlite:///./sql_app.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

metadata = MetaData(naming_convention=DB_NAMING_CONVENTION)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


session = SessionLocal()
