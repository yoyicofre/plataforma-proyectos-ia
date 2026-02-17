from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from src.core.project_authz import PROJECT_RW_ROLES, require_project_role
from src.core.security import User
from src.modules.users.dependencies import current_user, require_operator_or_admin
from src.modules.projects.dependencies import db_session
from src.modules.projects.schemas import ProjectCreate, ProjectOut, ProjectUpdate
from src.modules.projects.service import (
    create_project,
    get_project,
    list_projects_for_user,
    update_project,
)

router = APIRouter()


@router.get("/", response_model=list[ProjectOut])
def get_projects(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    user: User = Depends(current_user),
    db: Session = Depends(db_session),
) -> list[ProjectOut]:
    return list_projects_for_user(db=db, user_id=int(user.id), limit=limit, offset=offset)


@router.get("/{project_id}", response_model=ProjectOut)
def get_project_by_id(
    project_id: int,
    user: User = Depends(current_user),
    db: Session = Depends(db_session),
) -> ProjectOut:
    require_project_role(db=db, project_id=project_id, user=user, allowed_roles={"admin", "operator", "viewer"})
    return get_project(db=db, project_id=project_id)


@router.post("/", response_model=ProjectOut, status_code=201)
def post_project(
    payload: ProjectCreate,
    user: User = Depends(require_operator_or_admin),
    db: Session = Depends(db_session),
) -> ProjectOut:
    if payload.owner_user_id is None:
        payload.owner_user_id = int(user.id)
    return create_project(db=db, payload=payload)


@router.patch("/{project_id}", response_model=ProjectOut)
def patch_project(
    project_id: int,
    payload: ProjectUpdate,
    user: User = Depends(current_user),
    db: Session = Depends(db_session),
) -> ProjectOut:
    require_project_role(db=db, project_id=project_id, user=user, allowed_roles=PROJECT_RW_ROLES)
    return update_project(db=db, project_id=project_id, payload=payload)
