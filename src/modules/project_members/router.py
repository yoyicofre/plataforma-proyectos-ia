from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from src.core.project_authz import PROJECT_ALL_ROLES, require_project_role
from src.core.security import User
from src.modules.project_members.dependencies import db_session
from src.modules.project_members.schemas import (
    ProjectMemberCreate,
    ProjectMemberOut,
    ProjectMemberUpdate,
)
from src.modules.project_members.service import (
    create_member,
    delete_member,
    list_members,
    update_member,
)
from src.modules.users.dependencies import current_user

router = APIRouter()


@router.get("/projects/{project_id}/members", response_model=list[ProjectMemberOut])
def get_project_members(
    project_id: int,
    user: User = Depends(current_user),
    db: Session = Depends(db_session),
) -> list[ProjectMemberOut]:
    require_project_role(db=db, project_id=project_id, user=user, allowed_roles=PROJECT_ALL_ROLES)
    return list_members(db=db, project_id=project_id)


@router.post("/projects/{project_id}/members", response_model=ProjectMemberOut, status_code=201)
def post_project_member(
    project_id: int,
    payload: ProjectMemberCreate,
    user: User = Depends(current_user),
    db: Session = Depends(db_session),
) -> ProjectMemberOut:
    require_project_role(db=db, project_id=project_id, user=user, allowed_roles={"admin"})
    return create_member(db=db, project_id=project_id, payload=payload)


@router.patch("/projects/{project_id}/members/{member_user_id}", response_model=ProjectMemberOut)
def patch_project_member(
    project_id: int,
    member_user_id: int,
    payload: ProjectMemberUpdate,
    user: User = Depends(current_user),
    db: Session = Depends(db_session),
) -> ProjectMemberOut:
    require_project_role(db=db, project_id=project_id, user=user, allowed_roles={"admin"})
    return update_member(
        db=db,
        project_id=project_id,
        user_id=member_user_id,
        payload=payload,
    )


@router.delete("/projects/{project_id}/members/{member_user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project_member(
    project_id: int,
    member_user_id: int,
    user: User = Depends(current_user),
    db: Session = Depends(db_session),
) -> Response:
    require_project_role(db=db, project_id=project_id, user=user, allowed_roles={"admin"})
    delete_member(db=db, project_id=project_id, user_id=member_user_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
