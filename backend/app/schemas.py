from datetime import datetime
from typing import Any
from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class ResponseScenario(BaseModel):
    scenario: str = "success"
    status_code: int = Field(ge=100, le=599)
    headers: dict[str, str] = {}
    body: Any = None


class MockAPICreate(BaseModel):
    name: str
    path: str = Field(pattern=r"^/")
    method: str
    version: str = "v1"
    is_private: bool = False
    auth_required: bool = False
    response_delay_ms: int = Field(default=0, ge=0, le=30000)
    body_schema: dict[str, Any] | None = None
    required_headers: dict[str, str] | None = None
    required_params: dict[str, str] | None = None
    responses: list[ResponseScenario]


class MockAPIOut(BaseModel):
    id: int
    name: str
    path: str
    method: str
    is_active: bool
    is_private: bool
    auth_required: bool
    response_delay_ms: int
    created_at: datetime
    model_config = {"from_attributes": True}


class MockAPIStatusUpdate(BaseModel):
    is_active: bool


class MockAPIEdit(BaseModel):
    name: str
    path: str = Field(pattern=r"^/")
    method: str
    is_private: bool = False
    auth_required: bool = False
    response_delay_ms: int = Field(default=0, ge=0, le=30000)


class VersionCreate(BaseModel):
    version: str = Field(pattern=r"^v[0-9]+(?:\.[0-9]+)*$")
    make_current: bool = True


class PermissionCreate(BaseModel):
    email: EmailStr


class ResponseTemplateUpdate(ResponseScenario):
    pass
