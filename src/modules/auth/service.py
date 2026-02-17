import secrets

from sqlalchemy import text
from sqlalchemy.orm import Session

from src.core.config import settings
from src.core.errors import forbidden, not_found
from src.core.security import User, create_access_token
from src.modules.auth.schemas import (
    AuthLoginRequest,
    AuthTokenRequest,
    AuthTokenResponse,
    GlobalPermissionsMeOut,
)

ALLOWED_ROLES = {"admin", "operator", "viewer"}


def issue_dev_token(db: Session, payload: AuthTokenRequest) -> AuthTokenResponse:
    if settings.is_production:
        raise forbidden("Dev bootstrap token endpoint is disabled in production")
    if payload.bootstrap_key != settings.dev_bootstrap_key:
        raise forbidden("Invalid bootstrap key")

    row = (
        db.execute(
            text("SELECT user_id, email FROM users WHERE email = :email"),
            {"email": payload.email},
        )
        .mappings()
        .first()
    )
    if not row:
        raise not_found("User email not found")

    requested_roles = payload.roles or ["admin"]
    invalid_roles = [role for role in requested_roles if role not in ALLOWED_ROLES]
    if invalid_roles:
        raise forbidden(f"Invalid role(s): {invalid_roles}")

    token = create_access_token(
        user_id=int(row["user_id"]),
        email=str(row["email"]),
        roles=requested_roles,
    )
    return AuthTokenResponse(
        access_token=token,
        expires_in_seconds=settings.jwt_exp_minutes * 60,
    )


def _resolve_user_roles(db: Session, user_id: int) -> list[str]:
    rows = db.execute(
        text(
            """
            SELECT DISTINCT member_role
            FROM project_members
            WHERE user_id = :user_id
            """
        ),
        {"user_id": user_id},
    ).mappings()
    roles = sorted([str(r["member_role"]) for r in rows if r.get("member_role") in ALLOWED_ROLES])
    if roles:
        return roles
    return ["viewer"]


def issue_login_token(db: Session, payload: AuthLoginRequest) -> AuthTokenResponse:
    portal_key = settings.portal_access_key or settings.dev_bootstrap_key
    if not secrets.compare_digest(payload.access_key, portal_key):
        raise forbidden("Invalid credentials")

    row = (
        db.execute(
            text("SELECT user_id, email FROM users WHERE email = :email"),
            {"email": payload.email},
        )
        .mappings()
        .first()
    )
    if not row:
        raise not_found("User email not found")

    roles = _resolve_user_roles(db=db, user_id=int(row["user_id"]))
    token = create_access_token(
        user_id=int(row["user_id"]),
        email=str(row["email"]),
        roles=roles,
    )
    return AuthTokenResponse(
        access_token=token,
        expires_in_seconds=settings.jwt_exp_minutes * 60,
    )


def get_global_permissions_me(user: User) -> GlobalPermissionsMeOut:
    roles = sorted(list(user.roles))
    is_admin = "admin" in user.roles
    is_operator = "operator" in user.roles
    is_viewer = "viewer" in user.roles
    is_prod = settings.is_production

    return GlobalPermissionsMeOut(
        user_id=int(user.id),
        roles=roles,
        can_access_platform=is_admin or is_operator or is_viewer,
        can_create_projects=is_admin or is_operator,
        can_manage_agent_catalog=is_admin or is_operator,
        can_issue_dev_tokens=not is_prod and (is_admin or is_operator),
        can_manage_security=is_admin,
    )
