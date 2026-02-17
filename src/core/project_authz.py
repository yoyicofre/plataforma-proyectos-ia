from sqlalchemy import text
from sqlalchemy.orm import Session

from src.core.errors import forbidden, not_found
from src.core.security import User

PROJECT_RW_ROLES = {"admin", "operator"}
PROJECT_ALL_ROLES = {"admin", "operator", "viewer"}


def get_project_member_role(
    db: Session,
    project_id: int,
    user_id: int,
) -> str | None:
    role = db.execute(
        text(
            """
            SELECT member_role
            FROM project_members
            WHERE project_id = :project_id
              AND user_id = :user_id
            """
        ),
        {"project_id": project_id, "user_id": user_id},
    ).scalar_one_or_none()
    return str(role) if role is not None else None


def require_project_role(
    db: Session,
    project_id: int,
    user: User,
    allowed_roles: set[str],
) -> str:
    project_exists = db.execute(
        text("SELECT 1 FROM projects WHERE project_id = :project_id"),
        {"project_id": project_id},
    ).first()
    if not project_exists:
        raise not_found("Project not found")

    member_role = get_project_member_role(db, project_id, int(user.id))
    if member_role is None:
        raise forbidden("User is not a member of this project")
    if member_role not in allowed_roles:
        raise forbidden(f"Member role '{member_role}' not allowed for this action")
    return member_role
