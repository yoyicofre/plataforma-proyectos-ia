from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.core.errors import bad_request, conflict, forbidden, not_found
from src.modules.ia_generator.schemas import (
    IaConversationCreate,
    IaConversationDetailOut,
    IaConversationOut,
    IaMessageCreate,
    IaMessageOut,
    IaSavedOutputOut,
)

ALLOWED_MESSAGE_ROLES = {"system", "user", "assistant"}


def _map_conversation(row: dict) -> IaConversationOut:
    return IaConversationOut(**row)


def _map_message(row: dict) -> IaMessageOut:
    row["is_saved"] = bool(row.get("is_saved"))
    return IaMessageOut(**row)


def _map_saved_output(row: dict) -> IaSavedOutputOut:
    return IaSavedOutputOut(**row)


def _ensure_conversation_access(db: Session, conversation_id: int, user_id: int) -> IaConversationOut:
    row = (
        db.execute(
            text(
                """
                SELECT
                  c.conversation_id,
                  c.project_id,
                  c.agent_id,
                  c.title,
                  c.status,
                  c.created_by_user_id,
                  c.created_at,
                  c.updated_at
                FROM ia_conversations c
                JOIN project_members pm ON pm.project_id = c.project_id
                WHERE c.conversation_id = :conversation_id
                  AND pm.user_id = :user_id
                """
            ),
            {"conversation_id": conversation_id, "user_id": user_id},
        )
        .mappings()
        .first()
    )
    if row:
        return _map_conversation(dict(row))

    exists = db.execute(
        text("SELECT 1 FROM ia_conversations WHERE conversation_id = :conversation_id"),
        {"conversation_id": conversation_id},
    ).first()
    if not exists:
        raise not_found("Conversation not found")
    raise forbidden("User cannot access this conversation")


def create_conversation(db: Session, payload: IaConversationCreate, user_id: int) -> IaConversationOut:
    try:
        result = db.execute(
            text(
                """
                INSERT INTO ia_conversations (
                  project_id, agent_id, title, status, created_by_user_id
                ) VALUES (
                  :project_id, :agent_id, :title, 'draft', :created_by_user_id
                )
                """
            ),
            {
                "project_id": payload.project_id,
                "agent_id": payload.agent_id,
                "title": payload.title,
                "created_by_user_id": user_id,
            },
        )
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise conflict("Invalid project_id/agent_id/created_by_user_id") from exc

    return _ensure_conversation_access(db, int(result.lastrowid), user_id)


def list_conversations_for_user(
    db: Session,
    user_id: int,
    limit: int = 50,
    offset: int = 0,
    project_id: int | None = None,
    agent_id: int | None = None,
) -> list[IaConversationOut]:
    rows = (
        db.execute(
            text(
                """
                SELECT
                  c.conversation_id,
                  c.project_id,
                  c.agent_id,
                  c.title,
                  c.status,
                  c.created_by_user_id,
                  c.created_at,
                  c.updated_at
                FROM ia_conversations c
                JOIN project_members pm ON pm.project_id = c.project_id
                WHERE pm.user_id = :user_id
                  AND (:project_id IS NULL OR c.project_id = :project_id)
                  AND (:agent_id IS NULL OR c.agent_id = :agent_id)
                ORDER BY c.updated_at DESC, c.conversation_id DESC
                LIMIT :limit OFFSET :offset
                """
            ),
            {
                "user_id": user_id,
                "project_id": project_id,
                "agent_id": agent_id,
                "limit": limit,
                "offset": offset,
            },
        )
        .mappings()
        .all()
    )
    return [_map_conversation(dict(r)) for r in rows]


def get_conversation_detail_for_user(db: Session, conversation_id: int, user_id: int) -> IaConversationDetailOut:
    conv = _ensure_conversation_access(db, conversation_id=conversation_id, user_id=user_id)
    rows = (
        db.execute(
            text(
                """
                SELECT
                  message_id,
                  conversation_id,
                  role,
                  content,
                  provider,
                  model_name,
                  run_id,
                  cost_usd,
                  is_saved,
                  created_at
                FROM ia_messages
                WHERE conversation_id = :conversation_id
                ORDER BY message_id
                """
            ),
            {"conversation_id": conversation_id},
        )
        .mappings()
        .all()
    )
    return IaConversationDetailOut(
        conversation=conv,
        messages=[_map_message(dict(r)) for r in rows],
    )


def create_message_for_conversation(
    db: Session,
    conversation_id: int,
    payload: IaMessageCreate,
    user_id: int,
) -> IaMessageOut:
    _ = _ensure_conversation_access(db, conversation_id=conversation_id, user_id=user_id)
    if payload.role not in ALLOWED_MESSAGE_ROLES:
        raise bad_request(f"role must be one of: {sorted(ALLOWED_MESSAGE_ROLES)}")

    try:
        result = db.execute(
            text(
                """
                INSERT INTO ia_messages (
                  conversation_id, role, content, provider, model_name, run_id, cost_usd
                ) VALUES (
                  :conversation_id, :role, :content, :provider, :model_name, :run_id, :cost_usd
                )
                """
            ),
            {
                "conversation_id": conversation_id,
                "role": payload.role,
                "content": payload.content,
                "provider": payload.provider,
                "model_name": payload.model_name,
                "run_id": payload.run_id,
                "cost_usd": payload.cost_usd,
            },
        )

        db.execute(
            text(
                """
                UPDATE ia_conversations
                SET updated_at = CURRENT_TIMESTAMP
                WHERE conversation_id = :conversation_id
                """
            ),
            {"conversation_id": conversation_id},
        )
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise conflict("Invalid conversation_id/run_id for message") from exc

    row = (
        db.execute(
            text(
                """
                SELECT
                  message_id,
                  conversation_id,
                  role,
                  content,
                  provider,
                  model_name,
                  run_id,
                  cost_usd,
                  is_saved,
                  created_at
                FROM ia_messages
                WHERE message_id = :message_id
                """
            ),
            {"message_id": int(result.lastrowid)},
        )
        .mappings()
        .first()
    )
    if not row:
        raise bad_request("Message insert failed")
    return _map_message(dict(row))


def save_message_output(
    db: Session,
    message_id: int,
    label: str,
    notes: str | None,
    user_id: int,
) -> IaSavedOutputOut:
    row = (
        db.execute(
            text(
                """
                SELECT
                  m.message_id,
                  m.conversation_id,
                  m.role,
                  c.project_id
                FROM ia_messages m
                JOIN ia_conversations c ON c.conversation_id = m.conversation_id
                JOIN project_members pm ON pm.project_id = c.project_id
                WHERE m.message_id = :message_id
                  AND pm.user_id = :user_id
                """
            ),
            {"message_id": message_id, "user_id": user_id},
        )
        .mappings()
        .first()
    )
    if not row:
        exists = db.execute(
            text("SELECT 1 FROM ia_messages WHERE message_id = :message_id"),
            {"message_id": message_id},
        ).first()
        if not exists:
            raise not_found("Message not found")
        raise forbidden("User cannot save this message")

    if str(row["role"]) != "assistant":
        raise bad_request("Only assistant messages can be saved")

    try:
        result = db.execute(
            text(
                """
                INSERT INTO ia_saved_outputs (
                  conversation_id, message_id, label, notes, created_by_user_id
                ) VALUES (
                  :conversation_id, :message_id, :label, :notes, :created_by_user_id
                )
                """
            ),
            {
                "conversation_id": int(row["conversation_id"]),
                "message_id": message_id,
                "label": label,
                "notes": notes,
                "created_by_user_id": user_id,
            },
        )

        db.execute(
            text("UPDATE ia_messages SET is_saved = 1 WHERE message_id = :message_id"),
            {"message_id": message_id},
        )
        db.execute(
            text("UPDATE ia_conversations SET status = 'saved' WHERE conversation_id = :conversation_id"),
            {"conversation_id": int(row["conversation_id"])},
        )
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise conflict("Could not save output (possible duplicate relation)") from exc

    saved_row = (
        db.execute(
            text(
                """
                SELECT
                  s.saved_output_id,
                  s.conversation_id,
                  s.message_id,
                  s.label,
                  s.notes,
                  s.created_by_user_id,
                  s.created_at,
                  c.project_id,
                  c.agent_id,
                  m.run_id,
                  m.provider,
                  m.model_name,
                  m.content
                FROM ia_saved_outputs s
                JOIN ia_conversations c ON c.conversation_id = s.conversation_id
                JOIN ia_messages m ON m.message_id = s.message_id
                WHERE s.saved_output_id = :saved_output_id
                """
            ),
            {"saved_output_id": int(result.lastrowid)},
        )
        .mappings()
        .first()
    )
    if not saved_row:
        raise bad_request("Saved output insert failed")
    return _map_saved_output(dict(saved_row))


def list_saved_outputs_for_user(
    db: Session,
    user_id: int,
    limit: int = 50,
    offset: int = 0,
    project_id: int | None = None,
    agent_id: int | None = None,
) -> list[IaSavedOutputOut]:
    rows = (
        db.execute(
            text(
                """
                SELECT
                  s.saved_output_id,
                  s.conversation_id,
                  s.message_id,
                  s.label,
                  s.notes,
                  s.created_by_user_id,
                  s.created_at,
                  c.project_id,
                  c.agent_id,
                  m.run_id,
                  m.provider,
                  m.model_name,
                  m.content
                FROM ia_saved_outputs s
                JOIN ia_conversations c ON c.conversation_id = s.conversation_id
                JOIN ia_messages m ON m.message_id = s.message_id
                JOIN project_members pm ON pm.project_id = c.project_id
                WHERE pm.user_id = :user_id
                  AND (:project_id IS NULL OR c.project_id = :project_id)
                  AND (:agent_id IS NULL OR c.agent_id = :agent_id)
                ORDER BY s.saved_output_id DESC
                LIMIT :limit OFFSET :offset
                """
            ),
            {
                "user_id": user_id,
                "project_id": project_id,
                "agent_id": agent_id,
                "limit": limit,
                "offset": offset,
            },
        )
        .mappings()
        .all()
    )
    return [_map_saved_output(dict(r)) for r in rows]
