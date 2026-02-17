from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from src.core.project_authz import PROJECT_ALL_ROLES, PROJECT_RW_ROLES, require_project_role
from src.core.security import User
from src.modules.project_agent_assignments.dependencies import db_session
from src.modules.project_agent_assignments.schemas import (
    ProjectAgentAssignmentCreate,
    ProjectAgentAssignmentOut,
    ProjectAgentAssignmentUpdate,
)
from src.modules.project_agent_assignments.service import (
    create_assignment,
    get_assignment,
    list_assignments_for_user,
    update_assignment,
)
from src.modules.users.dependencies import current_user

router = APIRouter()


@router.get("/", response_model=list[ProjectAgentAssignmentOut])
def get_project_agent_assignments(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    project_id: int | None = Query(default=None, ge=1),
    agent_id: int | None = Query(default=None, ge=1),
    user: User = Depends(current_user),
    db: Session = Depends(db_session),
) -> list[ProjectAgentAssignmentOut]:
    if project_id is not None:
        require_project_role(db=db, project_id=project_id, user=user, allowed_roles=PROJECT_ALL_ROLES)
    return list_assignments_for_user(
        db=db,
        user_id=int(user.id),
        limit=limit,
        offset=offset,
        project_id=project_id,
        agent_id=agent_id,
    )


@router.get("/{assignment_id}", response_model=ProjectAgentAssignmentOut)
def get_project_agent_assignment(
    assignment_id: int,
    user: User = Depends(current_user),
    db: Session = Depends(db_session),
) -> ProjectAgentAssignmentOut:
    assignment = get_assignment(db=db, assignment_id=assignment_id)
    require_project_role(
        db=db,
        project_id=assignment.project_id,
        user=user,
        allowed_roles=PROJECT_ALL_ROLES,
    )
    return assignment


@router.post("/", response_model=ProjectAgentAssignmentOut, status_code=201)
def post_project_agent_assignment(
    payload: ProjectAgentAssignmentCreate,
    user: User = Depends(current_user),
    db: Session = Depends(db_session),
) -> ProjectAgentAssignmentOut:
    require_project_role(
        db=db,
        project_id=payload.project_id,
        user=user,
        allowed_roles=PROJECT_RW_ROLES,
    )
    if payload.assigned_by_user_id is None:
        payload.assigned_by_user_id = int(user.id)
    return create_assignment(db=db, payload=payload)


@router.patch("/{assignment_id}", response_model=ProjectAgentAssignmentOut)
def patch_project_agent_assignment(
    assignment_id: int,
    payload: ProjectAgentAssignmentUpdate,
    user: User = Depends(current_user),
    db: Session = Depends(db_session),
) -> ProjectAgentAssignmentOut:
    assignment = get_assignment(db=db, assignment_id=assignment_id)
    require_project_role(
        db=db,
        project_id=assignment.project_id,
        user=user,
        allowed_roles=PROJECT_RW_ROLES,
    )
    if payload.assigned_by_user_id is None:
        payload.assigned_by_user_id = int(user.id)
    return update_assignment(
        db=db,
        assignment_id=assignment_id,
        payload=payload,
    )
