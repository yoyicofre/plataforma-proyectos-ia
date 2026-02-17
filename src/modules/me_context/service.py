from sqlalchemy import text
from sqlalchemy.orm import Session

from src.core.security import User
from src.modules.auth.service import get_global_permissions_me
from src.modules.me_context.schemas import (
    MeContextOut,
    MeContextProfileOut,
    MeContextProjectOut,
)


def get_me_context(db: Session, user: User) -> MeContextOut:
    rows = (
        db.execute(
            text(
                """
                SELECT
                  p.project_id,
                  p.project_key,
                  p.project_name,
                  p.lifecycle_status,
                  p.updated_at,
                  pm.member_role
                FROM projects p
                JOIN project_members pm ON pm.project_id = p.project_id
                WHERE pm.user_id = :user_id
                ORDER BY p.updated_at DESC, p.project_id DESC
                """
            ),
            {"user_id": int(user.id)},
        )
        .mappings()
        .all()
    )

    projects = [MeContextProjectOut(**dict(row)) for row in rows]
    profile = MeContextProfileOut(
        user_id=int(user.id),
        email=user.email,
        roles=sorted(list(user.roles)),
    )
    global_permissions = get_global_permissions_me(user=user)
    return MeContextOut(
        profile=profile,
        global_permissions=global_permissions,
        projects=projects,
    )
