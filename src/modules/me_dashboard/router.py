from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from src.core.security import User
from src.modules.me_dashboard.dependencies import db_session
from src.modules.me_dashboard.schemas import MeDashboardOut
from src.modules.me_dashboard.service import get_me_dashboard
from src.modules.users.dependencies import current_user

router = APIRouter()


@router.get("/me/dashboard", response_model=MeDashboardOut)
def get_dashboard(
    limit: int = Query(default=20, ge=1, le=100),
    user: User = Depends(current_user),
    db: Session = Depends(db_session),
) -> MeDashboardOut:
    return get_me_dashboard(db=db, user=user, limit=limit)
