from datetime import datetime

from pydantic import BaseModel


class ProjectMemberCreate(BaseModel):
    user_id: int
    member_role: str


class ProjectMemberUpdate(BaseModel):
    member_role: str


class ProjectMemberOut(BaseModel):
    project_member_id: int
    project_id: int
    user_id: int
    member_role: str
    created_at: datetime
