from fastapi import Depends
from src.core.security import User, get_current_user, require_roles


def current_user(user: User = Depends(get_current_user)) -> User:
    return user


def require_admin(user: User = Depends(current_user)) -> User:
    require_roles(user, ["admin"])
    return user


def require_operator_or_admin(user: User = Depends(current_user)) -> User:
    require_roles(user, ["admin", "operator"])
    return user
