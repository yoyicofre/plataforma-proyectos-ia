from fastapi import Depends
from sqlalchemy.orm import Session

from src.core.db import get_db


def db_session(db: Session = Depends(get_db)) -> Session:
    return db
