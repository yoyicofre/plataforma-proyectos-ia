import json

from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.core.errors import bad_request
from src.modules.agent_runs.schemas import AgentRunCreate, AgentRunOut

ALLOWED_RUN_STATUS = {"queued", "running", "success", "failed", "cancelled", "timeout"}
ALLOWED_TRIGGER_SOURCE = {"manual", "schedule", "event", "api"}


def _json_load(value: object) -> dict | None:
    if value is None:
        return None
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        return json.loads(value)
    return None


def _map_row(row: dict) -> AgentRunOut:
    row["input_payload"] = _json_load(row.get("input_payload"))
    row["output_payload"] = _json_load(row.get("output_payload"))
    return AgentRunOut(**row)


def list_agent_runs(
    db: Session,
    limit: int = 50,
    offset: int = 0,
    project_id: int | None = None,
    agent_id: int | None = None,
) -> list[AgentRunOut]:
    rows = (
        db.execute(
            text(
                """
                SELECT
                  agent_run_id, project_id, agent_id, stage_id, provider, model_name, run_status, trigger_source,
                  input_payload, output_payload, error_message, started_at, finished_at,
                  duration_ms, token_input_count, token_output_count, cost_usd,
                  created_by_user_id, created_at
                FROM agent_runs
                WHERE (:project_id IS NULL OR project_id = :project_id)
                  AND (:agent_id IS NULL OR agent_id = :agent_id)
                ORDER BY agent_run_id DESC
                LIMIT :limit OFFSET :offset
                """
            ),
            {
                "project_id": project_id,
                "agent_id": agent_id,
                "limit": limit,
                "offset": offset,
            },
        )
        .mappings()
        .all()
    )
    return [_map_row(dict(r)) for r in rows]


def list_agent_runs_for_user(
    db: Session,
    user_id: int,
    limit: int = 50,
    offset: int = 0,
    project_id: int | None = None,
    agent_id: int | None = None,
) -> list[AgentRunOut]:
    rows = (
        db.execute(
            text(
                """
                SELECT
                  ar.agent_run_id, ar.project_id, ar.agent_id, ar.stage_id, ar.provider, ar.model_name, ar.run_status, ar.trigger_source,
                  ar.input_payload, ar.output_payload, ar.error_message, ar.started_at, ar.finished_at,
                  ar.duration_ms, ar.token_input_count, ar.token_output_count, ar.cost_usd,
                  ar.created_by_user_id, ar.created_at
                FROM agent_runs ar
                JOIN project_members pm ON pm.project_id = ar.project_id
                WHERE pm.user_id = :user_id
                  AND (:project_id IS NULL OR ar.project_id = :project_id)
                  AND (:agent_id IS NULL OR ar.agent_id = :agent_id)
                ORDER BY ar.agent_run_id DESC
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
    return [_map_row(dict(r)) for r in rows]


def create_agent_run(db: Session, payload: AgentRunCreate) -> AgentRunOut:
    if payload.run_status not in ALLOWED_RUN_STATUS:
        raise bad_request(f"run_status must be one of: {sorted(ALLOWED_RUN_STATUS)}")
    if payload.trigger_source not in ALLOWED_TRIGGER_SOURCE:
        raise bad_request(f"trigger_source must be one of: {sorted(ALLOWED_TRIGGER_SOURCE)}")

    try:
        result = db.execute(
            text(
                """
                INSERT INTO agent_runs (
                  project_id, agent_id, stage_id, provider, model_name, run_status, trigger_source,
                  input_payload, output_payload, error_message, duration_ms,
                  token_input_count, token_output_count, cost_usd, created_by_user_id
                ) VALUES (
                  :project_id, :agent_id, :stage_id, :provider, :model_name, :run_status, :trigger_source,
                  CAST(:input_payload AS JSON), CAST(:output_payload AS JSON), :error_message, :duration_ms,
                  :token_input_count, :token_output_count, :cost_usd, :created_by_user_id
                )
                """
            ),
            {
                **payload.model_dump(),
                "input_payload": json.dumps(payload.input_payload)
                if payload.input_payload is not None
                else None,
                "output_payload": json.dumps(payload.output_payload)
                if payload.output_payload is not None
                else None,
            },
        )
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise bad_request("Invalid project_id, agent_id, stage_id or created_by_user_id") from exc

    row = (
        db.execute(
            text(
                """
                SELECT
                  agent_run_id, project_id, agent_id, stage_id, provider, model_name, run_status, trigger_source,
                  input_payload, output_payload, error_message, started_at, finished_at,
                  duration_ms, token_input_count, token_output_count, cost_usd,
                  created_by_user_id, created_at
                FROM agent_runs
                WHERE agent_run_id = :agent_run_id
                """
            ),
            {"agent_run_id": result.lastrowid},
        )
        .mappings()
        .first()
    )
    if not row:
        raise bad_request("Agent run insert failed")
    return _map_row(dict(row))
