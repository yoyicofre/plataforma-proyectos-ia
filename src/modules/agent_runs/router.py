from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from src.core.project_authz import PROJECT_RW_ROLES, require_project_role
from src.core.security import User
from src.modules.agent_runs.dependencies import db_session
from src.modules.agent_runs.schemas import AgentRunCreate, AgentRunOut
from src.modules.agent_runs.service import create_agent_run, list_agent_runs_for_user
from src.modules.users.dependencies import current_user

router = APIRouter()


@router.get("/", response_model=list[AgentRunOut])
def get_agent_runs(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    project_id: int | None = Query(default=None, ge=1),
    agent_id: int | None = Query(default=None, ge=1),
    user: User = Depends(current_user),
    db: Session = Depends(db_session),
) -> list[AgentRunOut]:
    if project_id is not None:
        require_project_role(db=db, project_id=project_id, user=user, allowed_roles={"admin", "operator", "viewer"})
    return list_agent_runs_for_user(
        db=db,
        user_id=int(user.id),
        limit=limit,
        offset=offset,
        project_id=project_id,
        agent_id=agent_id,
    )


@router.post("/", response_model=AgentRunOut, status_code=201)
def post_agent_run(
    payload: AgentRunCreate,
    user: User = Depends(current_user),
    db: Session = Depends(db_session),
) -> AgentRunOut:
    require_project_role(
        db=db,
        project_id=payload.project_id,
        user=user,
        allowed_roles=PROJECT_RW_ROLES,
    )
    if payload.created_by_user_id is None:
        payload.created_by_user_id = int(user.id)
    return create_agent_run(db=db, payload=payload)
