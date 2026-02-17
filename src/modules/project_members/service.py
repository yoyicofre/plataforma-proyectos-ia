from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.core.errors import bad_request, conflict, not_found
from src.modules.project_members.schemas import (
    ProjectMemberCreate,
    ProjectMemberOut,
    ProjectMemberUpdate,
)

ALLOWED_MEMBER_ROLES = {"admin", "operator", "viewer"}


def _map_row(row: dict) -> ProjectMemberOut:
    return ProjectMemberOut(**row)


def list_members(db: Session, project_id: int) -> list[ProjectMemberOut]:
    rows = (
        db.execute(
            text(
                """
                SELECT
                  project_member_id,
                  project_id,
                  user_id,
                  member_role,
                  created_at
                FROM project_members
                WHERE project_id = :project_id
                ORDER BY project_member_id
                """
            ),
            {"project_id": project_id},
        )
        .mappings()
        .all()
    )
    return [_map_row(dict(r)) for r in rows]


def get_member(
    db: Session,
    project_id: int,
    user_id: int,
) -> ProjectMemberOut:
    row = (
        db.execute(
            text(
                """
                SELECT
                  project_member_id,
                  project_id,
                  user_id,
                  member_role,
                  created_at
                FROM project_members
                WHERE project_id = :project_id
                  AND user_id = :user_id
                """
            ),
            {"project_id": project_id, "user_id": user_id},
        )
        .mappings()
        .first()
    )
    if not row:
        raise not_found("Project member not found")
    return _map_row(dict(row))


def create_member(
    db: Session,
    project_id: int,
    payload: ProjectMemberCreate,
) -> ProjectMemberOut:
    if payload.member_role not in ALLOWED_MEMBER_ROLES:
        raise bad_request(f"member_role must be one of: {sorted(ALLOWED_MEMBER_ROLES)}")

    try:
        db.execute(
            text(
                """
                INSERT INTO project_members (
                  project_id, user_id, member_role
                ) VALUES (
                  :project_id, :user_id, :member_role
                )
                """
            ),
            {
                "project_id": project_id,
                "user_id": payload.user_id,
                "member_role": payload.member_role,
            },
        )
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise conflict("Invalid user_id/project_id or duplicated project member") from exc
    return get_member(db, project_id=project_id, user_id=payload.user_id)


def update_member(
    db: Session,
    project_id: int,
    user_id: int,
    payload: ProjectMemberUpdate,
) -> ProjectMemberOut:
    if payload.member_role not in ALLOWED_MEMBER_ROLES:
        raise bad_request(f"member_role must be one of: {sorted(ALLOWED_MEMBER_ROLES)}")

    current = get_member(db, project_id=project_id, user_id=user_id)
    owner_user_id = db.execute(
        text("SELECT owner_user_id FROM projects WHERE project_id = :project_id"),
        {"project_id": project_id},
    ).scalar_one_or_none()
    if owner_user_id is None:
        raise not_found("Project not found")

    if int(owner_user_id) == user_id and payload.member_role != "admin":
        raise bad_request("Project owner must keep admin role")

    if current.member_role == "admin" and payload.member_role != "admin":
        admin_count = db.execute(
            text(
                """
                SELECT COUNT(*) FROM project_members
                WHERE project_id = :project_id
                  AND member_role = 'admin'
                """
            ),
            {"project_id": project_id},
        ).scalar_one()
        if int(admin_count) <= 1:
            raise bad_request("Project must have at least one admin member")

    db.execute(
        text(
            """
            UPDATE project_members
            SET member_role = :member_role
            WHERE project_id = :project_id
              AND user_id = :user_id
            """
        ),
        {
            "member_role": payload.member_role,
            "project_id": project_id,
            "user_id": user_id,
        },
    )
    db.commit()
    return get_member(db, project_id=project_id, user_id=user_id)


def delete_member(db: Session, project_id: int, user_id: int) -> None:
    member = get_member(db, project_id=project_id, user_id=user_id)
    owner_user_id = db.execute(
        text("SELECT owner_user_id FROM projects WHERE project_id = :project_id"),
        {"project_id": project_id},
    ).scalar_one_or_none()
    if owner_user_id is None:
        raise not_found("Project not found")
    if int(owner_user_id) == user_id:
        raise bad_request("Project owner cannot be removed from project members")

    if member.member_role == "admin":
        admin_count = db.execute(
            text(
                """
                SELECT COUNT(*) FROM project_members
                WHERE project_id = :project_id
                  AND member_role = 'admin'
                """
            ),
            {"project_id": project_id},
        ).scalar_one()
        if int(admin_count) <= 1:
            raise bad_request("Project must have at least one admin member")

    db.execute(
        text(
            """
            DELETE FROM project_members
            WHERE project_id = :project_id
              AND user_id = :user_id
            """
        ),
        {"project_id": project_id, "user_id": user_id},
    )
    db.commit()
