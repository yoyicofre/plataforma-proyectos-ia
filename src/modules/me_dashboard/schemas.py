from datetime import datetime

from pydantic import BaseModel


class MeDashboardKpisOut(BaseModel):
    projects_count: int
    blocked_stages_count: int
    failed_runs_count_7d: int
    queued_runs_count: int
    published_artifacts_count: int
    cost_usd_total_30d: float


class MeDashboardProjectOut(BaseModel):
    project_id: int
    project_key: str
    project_name: str
    lifecycle_status: str
    member_role: str
    blocked_stages_count: int
    failed_runs_count_7d: int
    queued_runs_count: int
    cost_usd_total_30d: float
    updated_at: datetime


class MeDashboardOut(BaseModel):
    user_id: int
    generated_at: datetime
    kpis: MeDashboardKpisOut
    projects: list[MeDashboardProjectOut]
