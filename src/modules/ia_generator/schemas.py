from datetime import datetime

from pydantic import BaseModel, Field


class IaConversationCreate(BaseModel):
    project_id: int
    agent_id: int
    title: str | None = Field(default=None, max_length=180)


class IaConversationOut(BaseModel):
    conversation_id: int
    project_id: int
    agent_id: int
    title: str | None
    status: str
    created_by_user_id: int
    created_at: datetime
    updated_at: datetime


class IaMessageCreate(BaseModel):
    role: str
    content: str = Field(min_length=1, max_length=200000)
    provider: str | None = Field(default=None, max_length=40)
    model_name: str | None = Field(default=None, max_length=120)
    run_id: int | None = None
    cost_usd: float | None = None


class IaMessageOut(BaseModel):
    message_id: int
    conversation_id: int
    role: str
    content: str
    provider: str | None
    model_name: str | None
    run_id: int | None
    cost_usd: float | None
    is_saved: bool
    created_at: datetime


class IaConversationDetailOut(BaseModel):
    conversation: IaConversationOut
    messages: list[IaMessageOut]


class IaSaveMessageRequest(BaseModel):
    label: str = Field(min_length=2, max_length=180)
    notes: str | None = Field(default=None, max_length=1000)


class IaSavedOutputOut(BaseModel):
    saved_output_id: int
    conversation_id: int
    message_id: int
    label: str
    notes: str | None
    created_by_user_id: int
    created_at: datetime
    project_id: int
    agent_id: int
    run_id: int | None
    provider: str | None
    model_name: str | None
    content: str


class IaTextSpecialtyOut(BaseModel):
    code: str
    name: str
    description: str
    system_prompt_template: str
    recommended_provider: str
    recommended_model: str | None = None
    tags: list[str]
