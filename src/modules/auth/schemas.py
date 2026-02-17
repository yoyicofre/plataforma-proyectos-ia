from pydantic import BaseModel, Field


class AuthTokenRequest(BaseModel):
    email: str = Field(min_length=5, max_length=320)
    roles: list[str] | None = None
    bootstrap_key: str = Field(min_length=8, max_length=200)


class AuthTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in_seconds: int


class AuthLoginRequest(BaseModel):
    email: str = Field(min_length=5, max_length=320)
    access_key: str = Field(min_length=8, max_length=200)


class GlobalPermissionsMeOut(BaseModel):
    user_id: int
    roles: list[str]
    can_access_platform: bool
    can_create_projects: bool
    can_manage_agent_catalog: bool
    can_issue_dev_tokens: bool
    can_manage_security: bool
