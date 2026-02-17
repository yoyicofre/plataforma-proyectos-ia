from sqlalchemy.orm import Session

from src.core.project_authz import get_project_member_role, require_project_role
from src.core.security import User
from src.modules.project_permissions.schemas import ProjectPermissionsMeOut


def get_my_project_permissions(
    db: Session,
    project_id: int,
    user: User,
) -> ProjectPermissionsMeOut:
    role = require_project_role(
        db=db,
        project_id=project_id,
        user=user,
        allowed_roles={"admin", "operator", "viewer"},
    )
    member_role = get_project_member_role(db=db, project_id=project_id, user_id=int(user.id))
    if member_role is None:
        member_role = role

    can_rw = member_role in {"admin", "operator"}
    is_admin = member_role == "admin"

    return ProjectPermissionsMeOut(
        project_id=project_id,
        user_id=int(user.id),
        member_role=member_role,
        can_view_project=True,
        can_edit_project=can_rw,
        can_view_members=True,
        can_manage_members=is_admin,
        can_manage_stage_status=can_rw,
        can_manage_assignments=can_rw,
        can_create_agent_runs=can_rw,
    )
