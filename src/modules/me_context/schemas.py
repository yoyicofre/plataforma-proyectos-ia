from datetime import datetime

from pydantic import BaseModel

from src.modules.auth.schemas import GlobalPermissionsMeOut


class MeContextProjectOut(BaseModel):
    project_id: int
    project_key: str
    project_name: str
    lifecycle_status: str
    member_role: str
    updated_at: datetime


class MeContextProfileOut(BaseModel):
    user_id: int
    email: str | None
    roles: list[str]


class MeContextOut(BaseModel):
    profile: MeContextProfileOut
    global_permissions: GlobalPermissionsMeOut
    projects: list[MeContextProjectOut]
