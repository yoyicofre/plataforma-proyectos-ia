from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from src.core.project_authz import PROJECT_ALL_ROLES, require_project_role
from src.core.security import User
from src.modules.ia_generator.dependencies import db_session
from src.modules.ia_generator.schemas import (
    IaConversationCreate,
    IaConversationDetailOut,
    IaConversationOut,
    IaMessageCreate,
    IaMessageOut,
    IaSaveMessageRequest,
    IaSavedOutputOut,
    IaTextSpecialtyOut,
)
from src.modules.ia_generator.service import (
    create_conversation,
    create_message_for_conversation,
    get_conversation_detail_for_user,
    list_text_specialties,
    list_conversations_for_user,
    list_saved_outputs_for_user,
    save_message_output,
)
from src.modules.users.dependencies import current_user

router = APIRouter()


@router.get("/text-specialties", response_model=list[IaTextSpecialtyOut])
def get_text_specialties(
    user: User = Depends(current_user),
) -> list[IaTextSpecialtyOut]:
    _ = user
    return list_text_specialties()


@router.post("/conversations", response_model=IaConversationOut, status_code=201)
def post_conversation(
    payload: IaConversationCreate,
    user: User = Depends(current_user),
    db: Session = Depends(db_session),
) -> IaConversationOut:
    require_project_role(db=db, project_id=payload.project_id, user=user, allowed_roles=PROJECT_ALL_ROLES)
    return create_conversation(db=db, payload=payload, user_id=int(user.id))


@router.get("/conversations", response_model=list[IaConversationOut])
def get_conversations(
    project_id: int | None = Query(default=None, ge=1),
    agent_id: int | None = Query(default=None, ge=1),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    user: User = Depends(current_user),
    db: Session = Depends(db_session),
) -> list[IaConversationOut]:
    if project_id is not None:
        require_project_role(db=db, project_id=project_id, user=user, allowed_roles=PROJECT_ALL_ROLES)
    return list_conversations_for_user(
        db=db,
        user_id=int(user.id),
        project_id=project_id,
        agent_id=agent_id,
        limit=limit,
        offset=offset,
    )


@router.get("/conversations/{conversation_id}", response_model=IaConversationDetailOut)
def get_conversation(
    conversation_id: int,
    user: User = Depends(current_user),
    db: Session = Depends(db_session),
) -> IaConversationDetailOut:
    return get_conversation_detail_for_user(db=db, conversation_id=conversation_id, user_id=int(user.id))


@router.post("/conversations/{conversation_id}/messages", response_model=IaMessageOut, status_code=201)
def post_conversation_message(
    conversation_id: int,
    payload: IaMessageCreate,
    user: User = Depends(current_user),
    db: Session = Depends(db_session),
) -> IaMessageOut:
    return create_message_for_conversation(
        db=db,
        conversation_id=conversation_id,
        payload=payload,
        user_id=int(user.id),
    )


@router.post("/messages/{message_id}/save", response_model=IaSavedOutputOut, status_code=201)
def post_save_message(
    message_id: int,
    payload: IaSaveMessageRequest,
    user: User = Depends(current_user),
    db: Session = Depends(db_session),
) -> IaSavedOutputOut:
    return save_message_output(
        db=db,
        message_id=message_id,
        label=payload.label,
        notes=payload.notes,
        user_id=int(user.id),
    )


@router.get("/saved-outputs", response_model=list[IaSavedOutputOut])
def get_saved_outputs(
    project_id: int | None = Query(default=None, ge=1),
    agent_id: int | None = Query(default=None, ge=1),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    user: User = Depends(current_user),
    db: Session = Depends(db_session),
) -> list[IaSavedOutputOut]:
    if project_id is not None:
        require_project_role(db=db, project_id=project_id, user=user, allowed_roles=PROJECT_ALL_ROLES)
    return list_saved_outputs_for_user(
        db=db,
        user_id=int(user.id),
        project_id=project_id,
        agent_id=agent_id,
        limit=limit,
        offset=offset,
    )
