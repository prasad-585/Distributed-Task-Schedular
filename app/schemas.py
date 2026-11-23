from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field

class RegisterIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)

class LoginIn(BaseModel):
    email: EmailStr
    password: str

class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"

class TaskCreate(BaseModel):
    name: str = Field(min_length=1, max_length=150)
    task_type: str = "demo"
    payload: dict = {}
    scheduled_at: Optional[datetime] = None
    priority: int = Field(default=5, ge=1, le=10)
    interval_seconds: Optional[int] = Field(default=None, gt=0)
    max_retries: int = Field(default=3, ge=0, le=10)

class TaskUpdate(BaseModel):
    name: Optional[str] = None
    priority: Optional[int] = Field(default=None, ge=1, le=10)
    scheduled_at: Optional[datetime] = None
