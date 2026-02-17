from pydantic import BaseModel


class CostByProviderOut(BaseModel):
    provider: str
    total_cost_usd: float
    runs_count: int


class CostByModelOut(BaseModel):
    provider: str | None
    model_name: str | None
    total_cost_usd: float
    runs_count: int


class CostByProjectOut(BaseModel):
    project_id: int
    project_key: str
    project_name: str
    total_cost_usd: float
    runs_count: int


class CostSummaryOut(BaseModel):
    days: int
    project_id: int | None
    total_cost_usd: float
    total_runs_count: int
    by_provider: list[CostByProviderOut]
    by_model: list[CostByModelOut]
    by_project: list[CostByProjectOut]
