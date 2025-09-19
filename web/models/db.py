import uuid as uuid_lib
from contextlib import contextmanager
from datetime import datetime as dt
import os
from dotenv import load_dotenv
from sqlalchemy import Column, String, DateTime, func, create_engine
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base, sessionmaker
from pydantic import BaseModel, EmailStr, constr, validator
from typing import List, Optional


load_dotenv()

DATABASE_URL = (
    f"postgresql+psycopg2://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}"
    f"@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
)
engine = create_engine(
    DATABASE_URL,
    future=True,
    pool_pre_ping=True,
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
Base = declarative_base()

# Models
class Client(Base):
    __tablename__ = "clients"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid_lib.uuid4, index=True)
    first_name = Column(String(80), nullable=False)
    last_name  = Column(String(80), nullable=False)
    email = Column(String(254), nullable=False, unique=True, index=True)
    password_hash = Column(String(256), nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

class Meeting(Base):
    __tablename__ = "meetings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid_lib.uuid4, index=True)
    client_id = Column(String)
    title = Column(String)
    interviewee_name = Column(String)
    interviewee_email = Column(String)
    interviewer_name = Column(String)
    interviewer_email = Column(String)
    meeting_url = Column(String)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

# Schemas
PasswordStr = constr(min_length=8, max_length=128)

class SignupIn(BaseModel):
    first_name: constr(strip_whitespace=True, min_length=1, max_length=80)
    last_name:  constr(strip_whitespace=True, min_length=1, max_length=80)
    email: EmailStr
    password: PasswordStr

class SigninIn(BaseModel):
    email: EmailStr
    password: constr(min_length=1)

class AccountSettings(BaseModel):
    first_name: constr(strip_whitespace=True, min_length=1, max_length=80)
    last_name:  constr(strip_whitespace=True, min_length=1, max_length=80)
    email: EmailStr
    password: Optional[PasswordStr] = None

    @validator("password", pre=True, always=True)
    def empty_string_to_none(cls, v):
        if v is None or v == "":
            return None
        return

class APIError(BaseModel):
    field: str
    message: str

class APIResponse(BaseModel):
    ok: bool
    errors: List[APIError] = []
    redirect: Optional[str] = None

def get_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

Base.metadata.create_all(bind=engine)
