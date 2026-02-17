from pydantic import BaseModel, Field


class AiTextGenerateRequest(BaseModel):
    project_id: int
    agent_id: int
    prompt: str = Field(min_length=1, max_length=40000)
    system_prompt: str | None = None
    stage_id: int | None = None
    provider_preference: str = "auto"
    model_name: str | None = None
    temperature: float | None = Field(default=None, ge=0, le=2)
    max_output_tokens: int | None = Field(default=None, ge=1, le=16384)


class AiTextGenerateResponse(BaseModel):
    run_id: int
    provider: str
    model_name: str
    text: str
    token_input_count: int | None = None
    token_output_count: int | None = None
    cost_usd: float | None = None


class AiImageGenerateRequest(BaseModel):
    project_id: int
    agent_id: int
    prompt: str = Field(min_length=1, max_length=40000)
    stage_id: int | None = None
    provider_preference: str = "auto"
    model_name: str | None = None
    size: str | None = Field(default="1024x1024", max_length=30)


class AiImageGenerateResponse(BaseModel):
    run_id: int
    provider: str
    model_name: str
    mime_type: str | None = None
    image_base64: str | None = None
    image_url: str | None = None
    cost_usd: float | None = None
