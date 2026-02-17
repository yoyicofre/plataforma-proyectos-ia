from fastapi import APIRouter, Depends
from src.core.security import User
from src.modules.users.dependencies import current_user
from src.modules.users.schemas import UserOut
from src.modules.users.service import me

router = APIRouter()

@router.get("/me", response_model=UserOut)
def get_me(user: User = Depends(current_user)) -> UserOut:
    return me(user)
