import os
from datetime import datetime as dt
from dotenv import load_dotenv
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, Float, JSON
from pydantic import BaseModel, constr, HttpUrl
from sqlalchemy.orm import sessionmaker, declarative_base


load_dotenv()

DATABASE_URL = f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
Base = declarative_base()


# Models

class UserLogs(Base):
    __tablename__ = "user_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String)
    meeting_id = Column(String)
    log_id = Column(Integer)
    log = Column(JSON)
    fingerprint = Column(String)
    logged_at = Column(DateTime)
    created_at = Column(DateTime)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

if not os.getenv("TESTING"):
    Base.metadata.create_all(bind=engine)
