from datetime import datetime

from pydantic import BaseModel, Field


class AgentCreate(BaseModel):
    agent_code: str = Field(min_length=2, max_length=60)
    agent_name: str = Field(min_length=2, max_length=120)
    module_name: str = Field(min_length=2, max_length=80)
    owner_team: str = Field(min_length=2, max_length=120)
    default_model: str | None = Field(default=None, max_length=120)
    skill_ref: str | None = Field(default=None, max_length=255)
    is_active: bool = True
    metadata_json: dict | None = None


class AgentUpdate(BaseModel):
    agent_name: str | None = Field(default=None, min_length=2, max_length=120)
    module_name: str | None = Field(default=None, min_length=2, max_length=80)
    owner_team: str | None = Field(default=None, min_length=2, max_length=120)
    default_model: str | None = Field(default=None, max_length=120)
    skill_ref: str | None = Field(default=None, max_length=255)
    is_active: bool | None = None
    metadata_json: dict | None = None


class AgentOut(BaseModel):
    agent_id: int
    agent_code: str
    agent_name: str
    module_name: str
    owner_team: str
    default_model: str | None
    skill_ref: str | None
    is_active: bool
    metadata_json: dict | None
    created_at: datetime
    updated_at: datetime
