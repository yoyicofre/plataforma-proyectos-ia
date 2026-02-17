from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Iterable

import jwt
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from src.core.config import settings
from src.core.errors import unauthorized

bearer_scheme = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class User:
    id: int
    email: str | None
    roles: set[str]


def create_access_token(user_id: int, email: str | None, roles: list[str]) -> str:
    now = datetime.now(UTC)
    payload = {
        "sub": str(user_id),
        "email": email,
        "roles": roles,
        "iss": settings.jwt_issuer,
        "aud": settings.jwt_audience,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=settings.jwt_exp_minutes)).timestamp()),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> User:
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
            issuer=settings.jwt_issuer,
            audience=settings.jwt_audience,
        )
    except jwt.PyJWTError as exc:
        raise unauthorized("Invalid or expired token") from exc

    sub = payload.get("sub")
    if not sub:
        raise unauthorized("Token missing sub claim")
    roles = payload.get("roles") or []
    if not isinstance(roles, list):
        raise unauthorized("Token roles claim must be a list")

    try:
        user_id = int(sub)
    except ValueError as exc:
        raise unauthorized("Token sub claim must be numeric") from exc

    return User(
        id=user_id,
        email=payload.get("email"),
        roles={str(role) for role in roles},
    )


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> User:
    if credentials is None:
        raise unauthorized("Missing bearer token")
    return decode_access_token(credentials.credentials)


def require_roles(user: User, allowed: Iterable[str]) -> None:
    allowed_set = set(allowed)
    if user.roles.isdisjoint(allowed_set):
        from src.core.errors import forbidden

        raise forbidden("Missing required role(s)")
