from src.core.security import User
from src.modules.users.schemas import UserOut


def me(user: User) -> UserOut:
    return UserOut(id=int(user.id), roles=sorted(list(user.roles)))
