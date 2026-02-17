from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.core.security import User
from src.modules.project_permissions.dependencies import db_session
from src.modules.project_permissions.schemas import ProjectPermissionsMeOut
from src.modules.project_permissions.service import get_my_project_permissions
from src.modules.users.dependencies import current_user

router = APIRouter()


@router.get("/projects/{project_id}/permissions/me", response_model=ProjectPermissionsMeOut)
def get_project_permissions_me(
    project_id: int,
    user: User = Depends(current_user),
    db: Session = Depends(db_session),
) -> ProjectPermissionsMeOut:
    return get_my_project_permissions(db=db, project_id=project_id, user=user)
