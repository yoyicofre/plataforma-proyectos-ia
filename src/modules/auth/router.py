from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

from src.core.security import User
from src.core.db import get_db
from src.modules.auth.schemas import (
    AuthLoginRequest,
    AuthLogoutResponse,
    AuthTokenRequest,
    AuthTokenResponse,
    GlobalPermissionsMeOut,
)
from src.modules.auth.service import (
    get_global_permissions_me,
    issue_dev_token,
    issue_login_token,
    logout_user,
)
from src.modules.users.dependencies import current_user

router = APIRouter()


@router.post("/token", response_model=AuthTokenResponse)
def post_token(payload: AuthTokenRequest, db: Session = Depends(get_db)) -> AuthTokenResponse:
    return issue_dev_token(db=db, payload=payload)


@router.post("/login", response_model=AuthTokenResponse)
def post_login(payload: AuthLoginRequest, db: Session = Depends(get_db)) -> AuthTokenResponse:
    return issue_login_token(db=db, payload=payload)


@router.options("/login")
def options_login() -> Response:
    return Response(status_code=204)


@router.post("/logout", response_model=AuthLogoutResponse)
def post_logout(user: User = Depends(current_user)) -> AuthLogoutResponse:
    return logout_user(user=user)


@router.options("/logout")
def options_logout() -> Response:
    return Response(status_code=204)


@router.get("/permissions/me", response_model=GlobalPermissionsMeOut)
def get_permissions_me(user: User = Depends(current_user)) -> GlobalPermissionsMeOut:
    return get_global_permissions_me(user=user)
