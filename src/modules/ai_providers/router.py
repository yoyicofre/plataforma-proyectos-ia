from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.core.project_authz import PROJECT_RW_ROLES, require_project_role
from src.core.security import User
from src.modules.ai_providers.dependencies import db_session
from src.modules.ai_providers.schemas import (
    AiImageGenerateRequest,
    AiImageGenerateResponse,
    AiTextGenerateRequest,
    AiTextGenerateResponse,
)
from src.modules.ai_providers.service import generate_image, generate_text
from src.modules.users.dependencies import current_user

router = APIRouter()


@router.post("/text/generate", response_model=AiTextGenerateResponse)
def post_ai_text_generate(
    payload: AiTextGenerateRequest,
    user: User = Depends(current_user),
    db: Session = Depends(db_session),
) -> AiTextGenerateResponse:
    require_project_role(
        db=db,
        project_id=payload.project_id,
        user=user,
        allowed_roles=PROJECT_RW_ROLES,
    )
    return generate_text(db=db, user=user, req=payload)


@router.post("/image/generate", response_model=AiImageGenerateResponse)
def post_ai_image_generate(
    payload: AiImageGenerateRequest,
    user: User = Depends(current_user),
    db: Session = Depends(db_session),
) -> AiImageGenerateResponse:
    require_project_role(
        db=db,
        project_id=payload.project_id,
        user=user,
        allowed_roles=PROJECT_RW_ROLES,
    )
    return generate_image(db=db, user=user, req=payload)
