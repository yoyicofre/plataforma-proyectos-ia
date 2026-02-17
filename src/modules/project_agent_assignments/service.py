from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.core.errors import bad_request, conflict, not_found
from src.modules.project_agent_assignments.schemas import (
    ProjectAgentAssignmentCreate,
    ProjectAgentAssignmentOut,
    ProjectAgentAssignmentUpdate,
)

ALLOWED_ASSIGNMENT_STATUS = {"active", "paused", "disabled"}


def _map_row(row: dict) -> ProjectAgentAssignmentOut:
    return ProjectAgentAssignmentOut(**row)


def list_assignments(
    db: Session,
    limit: int = 50,
    offset: int = 0,
    project_id: int | None = None,
    agent_id: int | None = None,
) -> list[ProjectAgentAssignmentOut]:
    rows = (
        db.execute(
            text(
                """
                SELECT
                  paa.project_agent_assignment_id,
                  paa.project_id,
                  paa.agent_id,
                  paa.stage_id,
                  paa.assignment_status,
                  paa.assigned_at,
                  paa.assigned_by_user_id,
                  sc.stage_code,
                  sc.stage_name
                FROM project_agent_assignments paa
                LEFT JOIN stage_catalog sc ON sc.stage_id = paa.stage_id
                WHERE (:project_id IS NULL OR paa.project_id = :project_id)
                  AND (:agent_id IS NULL OR paa.agent_id = :agent_id)
                ORDER BY paa.project_agent_assignment_id DESC
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


def list_assignments_for_user(
    db: Session,
    user_id: int,
    limit: int = 50,
    offset: int = 0,
    project_id: int | None = None,
    agent_id: int | None = None,
) -> list[ProjectAgentAssignmentOut]:
    rows = (
        db.execute(
            text(
                """
                SELECT
                  paa.project_agent_assignment_id,
                  paa.project_id,
                  paa.agent_id,
                  paa.stage_id,
                  paa.assignment_status,
                  paa.assigned_at,
                  paa.assigned_by_user_id,
                  sc.stage_code,
                  sc.stage_name
                FROM project_agent_assignments paa
                JOIN project_members pm ON pm.project_id = paa.project_id
                LEFT JOIN stage_catalog sc ON sc.stage_id = paa.stage_id
                WHERE pm.user_id = :user_id
                  AND (:project_id IS NULL OR paa.project_id = :project_id)
                  AND (:agent_id IS NULL OR paa.agent_id = :agent_id)
                ORDER BY paa.project_agent_assignment_id DESC
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


def get_assignment(db: Session, assignment_id: int) -> ProjectAgentAssignmentOut:
    row = (
        db.execute(
            text(
                """
                SELECT
                  paa.project_agent_assignment_id,
                  paa.project_id,
                  paa.agent_id,
                  paa.stage_id,
                  paa.assignment_status,
                  paa.assigned_at,
                  paa.assigned_by_user_id,
                  sc.stage_code,
                  sc.stage_name
                FROM project_agent_assignments paa
                LEFT JOIN stage_catalog sc ON sc.stage_id = paa.stage_id
                WHERE paa.project_agent_assignment_id = :assignment_id
                """
            ),
            {"assignment_id": assignment_id},
        )
        .mappings()
        .first()
    )
    if not row:
        raise not_found("Project agent assignment not found")
    return _map_row(dict(row))


def create_assignment(db: Session, payload: ProjectAgentAssignmentCreate) -> ProjectAgentAssignmentOut:
    if payload.assignment_status not in ALLOWED_ASSIGNMENT_STATUS:
        raise bad_request(
            f"assignment_status must be one of: {sorted(ALLOWED_ASSIGNMENT_STATUS)}"
        )

    try:
        result = db.execute(
            text(
                """
                INSERT INTO project_agent_assignments (
                  project_id, agent_id, stage_id, assignment_status, assigned_by_user_id
                ) VALUES (
                  :project_id, :agent_id, :stage_id, :assignment_status, :assigned_by_user_id
                )
                """
            ),
            payload.model_dump(),
        )
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise conflict(
            "Invalid project_id/agent_id/stage_id or duplicated assignment tuple"
        ) from exc
    return get_assignment(db, int(result.lastrowid))


def update_assignment(
    db: Session,
    assignment_id: int,
    payload: ProjectAgentAssignmentUpdate,
) -> ProjectAgentAssignmentOut:
    _ = get_assignment(db, assignment_id)
    if payload.assignment_status not in ALLOWED_ASSIGNMENT_STATUS:
        raise bad_request(
            f"assignment_status must be one of: {sorted(ALLOWED_ASSIGNMENT_STATUS)}"
        )

    try:
        db.execute(
            text(
                """
                UPDATE project_agent_assignments
                SET assignment_status = :assignment_status,
                    assigned_by_user_id = :assigned_by_user_id
                WHERE project_agent_assignment_id = :assignment_id
                """
            ),
            {
                "assignment_status": payload.assignment_status,
                "assigned_by_user_id": payload.assigned_by_user_id,
                "assignment_id": assignment_id,
            },
        )
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise bad_request("Invalid assignment update payload") from exc
    return get_assignment(db, assignment_id)
