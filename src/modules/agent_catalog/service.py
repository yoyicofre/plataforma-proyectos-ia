import json

from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.core.errors import bad_request, conflict, not_found
from src.modules.agent_catalog.schemas import AgentCreate, AgentOut, AgentUpdate


def _json_load(value: object) -> dict | None:
    if value is None:
        return None
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        return json.loads(value)
    return None


def _map_row(row: dict) -> AgentOut:
    row["is_active"] = bool(row.get("is_active"))
    row["metadata_json"] = _json_load(row.get("metadata_json"))
    return AgentOut(**row)


def list_agents(
    db: Session,
    limit: int = 50,
    offset: int = 0,
    module_name: str | None = None,
    is_active: bool | None = None,
) -> list[AgentOut]:
    rows = (
        db.execute(
            text(
                """
                SELECT
                  agent_id, agent_code, agent_name, module_name, owner_team,
                  default_model, skill_ref, is_active, metadata_json,
                  created_at, updated_at
                FROM agent_catalog
                WHERE (:module_name IS NULL OR module_name = :module_name)
                  AND (:is_active IS NULL OR is_active = :is_active)
                ORDER BY agent_id DESC
                LIMIT :limit OFFSET :offset
                """
            ),
            {
                "module_name": module_name,
                "is_active": is_active,
                "limit": limit,
                "offset": offset,
            },
        )
        .mappings()
        .all()
    )
    return [_map_row(dict(r)) for r in rows]


def get_agent(db: Session, agent_id: int) -> AgentOut:
    row = (
        db.execute(
            text(
                """
                SELECT
                  agent_id, agent_code, agent_name, module_name, owner_team,
                  default_model, skill_ref, is_active, metadata_json,
                  created_at, updated_at
                FROM agent_catalog
                WHERE agent_id = :agent_id
                """
            ),
            {"agent_id": agent_id},
        )
        .mappings()
        .first()
    )
    if not row:
        raise not_found("Agent not found")
    return _map_row(dict(row))


def create_agent(db: Session, payload: AgentCreate) -> AgentOut:
    try:
        result = db.execute(
            text(
                """
                INSERT INTO agent_catalog (
                  agent_code, agent_name, module_name, owner_team,
                  default_model, skill_ref, is_active, metadata_json
                ) VALUES (
                  :agent_code, :agent_name, :module_name, :owner_team,
                  :default_model, :skill_ref, :is_active,
                  CAST(:metadata_json AS JSON)
                )
                """
            ),
            {
                **payload.model_dump(),
                "metadata_json": json.dumps(payload.metadata_json)
                if payload.metadata_json is not None
                else None,
            },
        )
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise conflict("Duplicated agent_code or invalid payload") from exc

    return get_agent(db, int(result.lastrowid))


def update_agent(db: Session, agent_id: int, payload: AgentUpdate) -> AgentOut:
    current = get_agent(db, agent_id)
    update_values = payload.model_dump(exclude_unset=True)
    if not update_values:
        return current

    fields: list[str] = []
    params: dict[str, object] = {"agent_id": agent_id}
    for key, value in update_values.items():
        if key == "metadata_json":
            fields.append("metadata_json = CAST(:metadata_json AS JSON)")
            params[key] = json.dumps(value) if value is not None else None
            continue
        fields.append(f"{key} = :{key}")
        params[key] = value

    try:
        db.execute(
            text(f"UPDATE agent_catalog SET {', '.join(fields)} WHERE agent_id = :agent_id"),
            params,
        )
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise bad_request("Invalid agent update payload") from exc
    return get_agent(db, agent_id)
