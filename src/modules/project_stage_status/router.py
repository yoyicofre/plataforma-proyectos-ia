from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.core.project_authz import PROJECT_ALL_ROLES, PROJECT_RW_ROLES, require_project_role
from src.core.security import User
from src.modules.project_stage_status.dependencies import db_session
from src.modules.project_stage_status.schemas import (
    ProjectStageStatusOut,
    ProjectStageStatusUpdate,
)
from src.modules.project_stage_status.service import (
    list_project_stage_status,
    update_project_stage_status,
)
from src.modules.users.dependencies import current_user

router = APIRouter()


@router.get("/projects/{project_id}/stages", response_model=list[ProjectStageStatusOut])
def get_project_stages(
    project_id: int,
    user: User = Depends(current_user),
    db: Session = Depends(db_session),
) -> list[ProjectStageStatusOut]:
    require_project_role(db=db, project_id=project_id, user=user, allowed_roles=PROJECT_ALL_ROLES)
    return list_project_stage_status(db=db, project_id=project_id)


@router.put(
    "/projects/{project_id}/stages/{stage_code}",
    response_model=ProjectStageStatusOut,
)
def put_project_stage_status(
    project_id: int,
    stage_code: str,
    payload: ProjectStageStatusUpdate,
    user: User = Depends(current_user),
    db: Session = Depends(db_session),
) -> ProjectStageStatusOut:
    require_project_role(db=db, project_id=project_id, user=user, allowed_roles=PROJECT_RW_ROLES)
    if payload.updated_by_user_id is None:
        payload.updated_by_user_id = int(user.id)
    return update_project_stage_status(
        db=db,
        project_id=project_id,
        stage_code=stage_code,
        payload=payload,
    )
