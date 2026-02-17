from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.core.security import User
from src.modules.me_context.dependencies import db_session
from src.modules.me_context.schemas import MeContextOut
from src.modules.me_context.service import get_me_context
from src.modules.users.dependencies import current_user

router = APIRouter()


@router.get("/me/context", response_model=MeContextOut)
def get_context(
    user: User = Depends(current_user),
    db: Session = Depends(db_session),
) -> MeContextOut:
    return get_me_context(db=db, user=user)
