from datetime import datetime

from pydantic import BaseModel, Field


class ProjectAgentAssignmentCreate(BaseModel):
    project_id: int
    agent_id: int
    stage_id: int | None = None
    assignment_status: str = Field(default="active")
    assigned_by_user_id: int | None = None


class ProjectAgentAssignmentUpdate(BaseModel):
    assignment_status: str = Field(default="active")
    assigned_by_user_id: int | None = None


class ProjectAgentAssignmentOut(BaseModel):
    project_agent_assignment_id: int
    project_id: int
    agent_id: int
    stage_id: int | None
    assignment_status: str
    assigned_at: datetime
    assigned_by_user_id: int | None
    stage_code: str | None
    stage_name: str | None
