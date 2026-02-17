from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from src.core.security import User
from src.modules.agent_catalog.dependencies import db_session
from src.modules.agent_catalog.schemas import AgentCreate, AgentOut, AgentUpdate
from src.modules.agent_catalog.service import create_agent, get_agent, list_agents, update_agent
from src.modules.users.dependencies import current_user, require_operator_or_admin

router = APIRouter()


@router.get("/", response_model=list[AgentOut])
def get_agents(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    module_name: str | None = Query(default=None),
    is_active: bool | None = Query(default=None),
    user: User = Depends(current_user),
    db: Session = Depends(db_session),
) -> list[AgentOut]:
    _ = user
    return list_agents(
        db=db,
        limit=limit,
        offset=offset,
        module_name=module_name,
        is_active=is_active,
    )


@router.get("/{agent_id}", response_model=AgentOut)
def get_agent_by_id(
    agent_id: int,
    user: User = Depends(current_user),
    db: Session = Depends(db_session),
) -> AgentOut:
    _ = user
    return get_agent(db=db, agent_id=agent_id)


@router.post("/", response_model=AgentOut, status_code=201)
def post_agent(
    payload: AgentCreate,
    user: User = Depends(require_operator_or_admin),
    db: Session = Depends(db_session),
) -> AgentOut:
    _ = user
    return create_agent(db=db, payload=payload)


@router.patch("/{agent_id}", response_model=AgentOut)
def patch_agent(
    agent_id: int,
    payload: AgentUpdate,
    user: User = Depends(require_operator_or_admin),
    db: Session = Depends(db_session),
) -> AgentOut:
    _ = user
    return update_agent(db=db, agent_id=agent_id, payload=payload)
