from datetime import datetime
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from .database import Base


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class MockAPI(Base):
    __tablename__ = "mock_apis"
    id: Mapped[int] = mapped_column(primary_key=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    name: Mapped[str] = mapped_column(String(120))
    path: Mapped[str] = mapped_column(String(500), index=True)
    method: Mapped[str] = mapped_column(String(10), index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_private: Mapped[bool] = mapped_column(Boolean, default=False)
    auth_required: Mapped[bool] = mapped_column(Boolean, default=False)
    response_delay_ms: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class APIVersion(Base):
    __tablename__ = "api_versions"
    id: Mapped[int] = mapped_column(primary_key=True)
    mock_api_id: Mapped[int] = mapped_column(ForeignKey("mock_apis.id"), index=True)
    version: Mapped[str] = mapped_column(String(30), default="v1")
    is_current: Mapped[bool] = mapped_column(Boolean, default=True)


class RequestSchema(Base):
    __tablename__ = "request_schemas"
    id: Mapped[int] = mapped_column(primary_key=True)
    mock_api_id: Mapped[int] = mapped_column(ForeignKey("mock_apis.id"), unique=True)
    body_schema: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    required_headers: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    required_params: Mapped[dict | None] = mapped_column(JSON, nullable=True)


class ResponseTemplate(Base):
    __tablename__ = "response_templates"
    id: Mapped[int] = mapped_column(primary_key=True)
    mock_api_id: Mapped[int] = mapped_column(ForeignKey("mock_apis.id"), index=True)
    scenario: Mapped[str] = mapped_column(String(50), default="success")
    status_code: Mapped[int] = mapped_column(Integer, default=200)
    headers: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    body: Mapped[dict | list | str | None] = mapped_column(JSON, nullable=True)


class RequestLog(Base):
    __tablename__ = "request_logs"
    id: Mapped[int] = mapped_column(primary_key=True)
    mock_api_id: Mapped[int] = mapped_column(ForeignKey("mock_apis.id"), index=True)
    method: Mapped[str] = mapped_column(String(10))
    path: Mapped[str] = mapped_column(String(500))
    request_params: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    request_body: Mapped[dict | list | str | None] = mapped_column(JSON, nullable=True)
    response_status: Mapped[int] = mapped_column(Integer)
    response_time_ms: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)


class APIPermission(Base):
    __tablename__ = "api_permissions"
    id: Mapped[int] = mapped_column(primary_key=True)
    mock_api_id: Mapped[int] = mapped_column(ForeignKey("mock_apis.id"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
