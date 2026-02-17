from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.core.errors import bad_request, not_found
from src.modules.project_stage_status.schemas import (
    ProjectStageStatusOut,
    ProjectStageStatusUpdate,
)

ALLOWED_STAGE_STATUS = {
    "not_started",
    "in_progress",
    "blocked",
    "done",
    "failed",
    "skipped",
}


def _map_row(row: dict) -> ProjectStageStatusOut:
    return ProjectStageStatusOut(**row)


def list_project_stage_status(db: Session, project_id: int) -> list[ProjectStageStatusOut]:
    rows = (
        db.execute(
            text(
                """
                SELECT
                  pss.project_stage_status_id,
                  pss.project_id,
                  pss.stage_id,
                  sc.stage_code,
                  sc.stage_name,
                  sc.stage_order,
                  pss.stage_status,
                  pss.started_at,
                  pss.completed_at,
                  pss.progress_percent,
                  pss.updated_by_user_id,
                  pss.updated_at
                FROM project_stage_status pss
                JOIN stage_catalog sc ON sc.stage_id = pss.stage_id
                WHERE pss.project_id = :project_id
                ORDER BY sc.stage_order
                """
            ),
            {"project_id": project_id},
        )
        .mappings()
        .all()
    )
    return [_map_row(dict(r)) for r in rows]


def update_project_stage_status(
    db: Session,
    project_id: int,
    stage_code: str,
    payload: ProjectStageStatusUpdate,
) -> ProjectStageStatusOut:
    stage = (
        db.execute(
            text("SELECT stage_id FROM stage_catalog WHERE stage_code = :stage_code"),
            {"stage_code": stage_code},
        )
        .mappings()
        .first()
    )
    if not stage:
        raise not_found("Stage not found")

    project_exists = db.execute(
        text("SELECT 1 FROM projects WHERE project_id = :project_id"),
        {"project_id": project_id},
    ).first()
    if not project_exists:
        raise not_found("Project not found")

    stage_id = int(stage["stage_id"])
    if payload.stage_status not in ALLOWED_STAGE_STATUS:
        raise bad_request(f"stage_status must be one of: {sorted(ALLOWED_STAGE_STATUS)}")

    started_at_sql = "NULL"
    completed_at_sql = "NULL"
    if payload.stage_status == "in_progress":
        started_at_sql = "CURRENT_TIMESTAMP"
    if payload.stage_status in {"done", "failed", "skipped"}:
        completed_at_sql = "CURRENT_TIMESTAMP"
    if payload.stage_status == "done" and payload.progress_percent < 100:
        raise bad_request("progress_percent must be 100 when stage_status is done")

    db.execute(
        text(
            f"""
            INSERT INTO project_stage_status (
              project_id, stage_id, stage_status, progress_percent, updated_by_user_id, started_at, completed_at
            ) VALUES (
              :project_id, :stage_id, :stage_status, :progress_percent, :updated_by_user_id, {started_at_sql}, {completed_at_sql}
            )
            ON DUPLICATE KEY UPDATE
              stage_status = VALUES(stage_status),
              progress_percent = VALUES(progress_percent),
              updated_by_user_id = VALUES(updated_by_user_id),
              started_at = COALESCE(project_stage_status.started_at, VALUES(started_at)),
              completed_at = VALUES(completed_at)
            """
        ),
        {
            "project_id": project_id,
            "stage_id": stage_id,
            "stage_status": payload.stage_status,
            "progress_percent": payload.progress_percent,
            "updated_by_user_id": payload.updated_by_user_id,
        },
    )

    try:
        db.execute(
            text(
                """
                INSERT INTO project_stage_events (
                  project_id, stage_id, event_type, event_payload, event_note, created_by_user_id
                ) VALUES (
                  :project_id,
                  :stage_id,
                  'status_change',
                  JSON_OBJECT('stage_status', :stage_status, 'progress_percent', :progress_percent),
                  :event_note,
                  :created_by_user_id
                )
                """
            ),
            {
                "project_id": project_id,
                "stage_id": stage_id,
                "stage_status": payload.stage_status,
                "progress_percent": payload.progress_percent,
                "event_note": payload.event_note,
                "created_by_user_id": payload.updated_by_user_id,
            },
        )
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise bad_request("Invalid user_id in stage update") from exc

    row = (
        db.execute(
            text(
                """
                SELECT
                  pss.project_stage_status_id,
                  pss.project_id,
                  pss.stage_id,
                  sc.stage_code,
                  sc.stage_name,
                  sc.stage_order,
                  pss.stage_status,
                  pss.started_at,
                  pss.completed_at,
                  pss.progress_percent,
                  pss.updated_by_user_id,
                  pss.updated_at
                FROM project_stage_status pss
                JOIN stage_catalog sc ON sc.stage_id = pss.stage_id
                WHERE pss.project_id = :project_id
                  AND pss.stage_id = :stage_id
                """
            ),
            {"project_id": project_id, "stage_id": stage_id},
        )
        .mappings()
        .first()
    )
    if not row:
        raise not_found("Project stage status not found")
    return _map_row(dict(row))
