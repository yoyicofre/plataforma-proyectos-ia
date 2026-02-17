from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.core.errors import bad_request, conflict, not_found
from src.modules.projects.schemas import ProjectCreate, ProjectOut, ProjectUpdate

ALLOWED_LIFECYCLE_STATUS = {"draft", "active", "paused", "completed", "cancelled"}


def _row_to_project(row: dict) -> ProjectOut:
    return ProjectOut(**row)


def list_projects(db: Session, limit: int = 50, offset: int = 0) -> list[ProjectOut]:
    rows = (
        db.execute(
            text(
                """
                SELECT
                  project_id, project_key, project_name, description,
                  lifecycle_status, owner_user_id, created_at, updated_at
                FROM projects
                ORDER BY project_id DESC
                LIMIT :limit OFFSET :offset
                """
            ),
            {"limit": limit, "offset": offset},
        )
        .mappings()
        .all()
    )
    return [_row_to_project(dict(r)) for r in rows]


def list_projects_for_user(
    db: Session,
    user_id: int,
    limit: int = 50,
    offset: int = 0,
) -> list[ProjectOut]:
    rows = (
        db.execute(
            text(
                """
                SELECT
                  p.project_id, p.project_key, p.project_name, p.description,
                  p.lifecycle_status, p.owner_user_id, p.created_at, p.updated_at
                FROM projects p
                JOIN project_members pm ON pm.project_id = p.project_id
                WHERE pm.user_id = :user_id
                ORDER BY p.project_id DESC
                LIMIT :limit OFFSET :offset
                """
            ),
            {"user_id": user_id, "limit": limit, "offset": offset},
        )
        .mappings()
        .all()
    )
    return [_row_to_project(dict(r)) for r in rows]


def get_project(db: Session, project_id: int) -> ProjectOut:
    row = (
        db.execute(
            text(
                """
                SELECT
                  project_id, project_key, project_name, description,
                  lifecycle_status, owner_user_id, created_at, updated_at
                FROM projects
                WHERE project_id = :project_id
                """
            ),
            {"project_id": project_id},
        )
        .mappings()
        .first()
    )
    if not row:
        raise not_found("Project not found")
    return _row_to_project(dict(row))


def create_project(db: Session, payload: ProjectCreate) -> ProjectOut:
    if payload.owner_user_id is None:
        raise bad_request("owner_user_id is required")
    if payload.lifecycle_status not in ALLOWED_LIFECYCLE_STATUS:
        raise bad_request(f"lifecycle_status must be one of: {sorted(ALLOWED_LIFECYCLE_STATUS)}")

    try:
        result = db.execute(
            text(
                """
                INSERT INTO projects (
                  project_key, project_name, description, lifecycle_status, owner_user_id
                ) VALUES (
                  :project_key, :project_name, :description, :lifecycle_status, :owner_user_id
                )
                """
            ),
            payload.model_dump(),
        )
        project_id = result.lastrowid

        db.execute(
            text(
                """
                INSERT INTO project_members (
                  project_id, user_id, member_role
                ) VALUES (
                  :project_id, :owner_user_id, 'admin'
                )
                ON DUPLICATE KEY UPDATE member_role = VALUES(member_role)
                """
            ),
            {"project_id": project_id, "owner_user_id": payload.owner_user_id},
        )

        db.execute(
            text(
                """
                INSERT INTO project_stage_status (
                  project_id, stage_id, stage_status, progress_percent
                )
                SELECT :project_id, stage_id, 'not_started', 0.00
                FROM stage_catalog
                """
            ),
            {"project_id": project_id},
        )
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise conflict("Invalid owner_user_id or duplicated project_key") from exc

    return get_project(db, int(project_id))


def update_project(db: Session, project_id: int, payload: ProjectUpdate) -> ProjectOut:
    current = get_project(db, project_id)
    update_values = payload.model_dump(exclude_unset=True)
    if not update_values:
        return current
    lifecycle_status = update_values.get("lifecycle_status")
    if lifecycle_status and lifecycle_status not in ALLOWED_LIFECYCLE_STATUS:
        raise bad_request(f"lifecycle_status must be one of: {sorted(ALLOWED_LIFECYCLE_STATUS)}")

    fields = []
    params: dict[str, object] = {"project_id": project_id}
    for key, value in update_values.items():
        fields.append(f"{key} = :{key}")
        params[key] = value

    db.execute(
        text(f"UPDATE projects SET {', '.join(fields)} WHERE project_id = :project_id"),
        params,
    )
    db.commit()
    return get_project(db, project_id)
