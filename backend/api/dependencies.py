from collections.abc import Generator

from fastapi import HTTPException
from sqlalchemy.orm import Session

from backend.db import SessionLocal


def get_db() -> Generator[Session, None, None]:
    if SessionLocal is None:
        raise HTTPException(status_code=500, detail="DATABASE_URL nao configurada.")

    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
