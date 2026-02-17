from datetime import datetime

from pydantic import BaseModel, Field


class AgentRunCreate(BaseModel):
    project_id: int
    agent_id: int
    stage_id: int | None = None
    provider: str | None = None
    model_name: str | None = None
    run_status: str = "queued"
    trigger_source: str = "manual"
    input_payload: dict | None = None
    output_payload: dict | None = None
    error_message: str | None = Field(default=None, max_length=1000)
    duration_ms: int | None = None
    token_input_count: int | None = None
    token_output_count: int | None = None
    cost_usd: float | None = None
    created_by_user_id: int | None = None


class AgentRunOut(BaseModel):
    agent_run_id: int
    project_id: int
    agent_id: int
    stage_id: int | None
    provider: str | None
    model_name: str | None
    run_status: str
    trigger_source: str
    input_payload: dict | None
    output_payload: dict | None
    error_message: str | None
    started_at: datetime | None
    finished_at: datetime | None
    duration_ms: int | None
    token_input_count: int | None
    token_output_count: int | None
    cost_usd: float | None
    created_by_user_id: int | None
    created_at: datetime
