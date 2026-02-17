from datetime import datetime

from pydantic import BaseModel, Field


class ProjectStageStatusOut(BaseModel):
    project_stage_status_id: int
    project_id: int
    stage_id: int
    stage_code: str
    stage_name: str
    stage_order: int
    stage_status: str
    started_at: datetime | None
    completed_at: datetime | None
    progress_percent: float
    updated_by_user_id: int | None
    updated_at: datetime


class ProjectStageStatusUpdate(BaseModel):
    stage_status: str
    progress_percent: float = Field(default=0.0, ge=0, le=100)
    updated_by_user_id: int | None = None
    event_note: str | None = Field(default=None, max_length=500)
