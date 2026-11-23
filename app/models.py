from datetime import datetime, timezone
from typing import Optional
from sqlmodel import SQLModel, Field

def utcnow():
    return datetime.now(timezone.utc)

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(index=True, unique=True)
    password_hash: str
    created_at: datetime = Field(default_factory=utcnow)

class Task(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    name: str
    task_type: str = "demo"
    payload: str = "{}"
    status: str = Field(default="pending", index=True)
    priority: int = Field(default=5, index=True)  # lower number = higher priority
    scheduled_at: datetime = Field(default_factory=utcnow, index=True)
    interval_seconds: Optional[int] = None
    is_recurring: bool = False
    max_retries: int = 3
    retry_count: int = 0
    cancel_requested: bool = False
    error_message: Optional[str] = None
    created_at: datetime = Field(default_factory=utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    next_retry_at: Optional[datetime] = None

class TaskLog(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    task_id: int = Field(index=True)
    message: str
    created_at: datetime = Field(default_factory=utcnow)

class DeadLetterTask(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    original_task_id: int = Field(index=True)
    user_id: int = Field(index=True)
    task_name: str
    error_message: str
    retry_count: int
    failed_at: datetime = Field(default_factory=utcnow)
    resolved: bool = False
