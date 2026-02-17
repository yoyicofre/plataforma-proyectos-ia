from datetime import datetime

from pydantic import BaseModel, Field


class ProjectCreate(BaseModel):
    project_key: str = Field(min_length=2, max_length=40)
    project_name: str = Field(min_length=2, max_length=180)
    description: str | None = None
    owner_user_id: int | None = None
    lifecycle_status: str = "draft"


class ProjectUpdate(BaseModel):
    project_name: str | None = Field(default=None, min_length=2, max_length=180)
    description: str | None = None
    lifecycle_status: str | None = None


class ProjectOut(BaseModel):
    project_id: int
    project_key: str
    project_name: str
    description: str | None
    lifecycle_status: str
    owner_user_id: int
    created_at: datetime
    updated_at: datetime
