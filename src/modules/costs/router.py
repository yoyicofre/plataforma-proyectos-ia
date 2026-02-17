from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from src.core.project_authz import PROJECT_ALL_ROLES, require_project_role
from src.core.security import User
from src.modules.costs.dependencies import db_session
from src.modules.costs.schemas import CostSummaryOut
from src.modules.costs.service import get_cost_summary
from src.modules.users.dependencies import current_user

router = APIRouter()


@router.get("/summary", response_model=CostSummaryOut)
def get_costs_summary(
    days: int = Query(default=30, ge=1, le=365),
    project_id: int | None = Query(default=None, ge=1),
    user: User = Depends(current_user),
    db: Session = Depends(db_session),
) -> CostSummaryOut:
    if project_id is not None:
        require_project_role(
            db=db,
            project_id=project_id,
            user=user,
            allowed_roles=PROJECT_ALL_ROLES,
        )
    return get_cost_summary(db=db, user=user, days=days, project_id=project_id)
