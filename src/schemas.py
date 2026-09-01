from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date, datetime

class TaskBase(BaseModel):
    title: str
    status: str = "pending"
    assigned_by: Optional[str] = None
    date_assigned: Optional[datetime] = None

class TaskCreate(TaskBase):
    pass

class TaskResponse(TaskBase):
    id: int
    user_id: int

    class Config:
        from_attributes = True

class UserBase(BaseModel):
    name: str
    username: str
    email: str
    learning_goal: str = "General"

class UserCreate(UserBase):
    password: str = Field(min_length=8, max_length=128)

class UserUpdate(BaseModel):
    name: Optional[str] = None
    learning_goal: Optional[str] = None

class DailyLogBase(BaseModel):
    hours_studied: float = Field(
        ge=0.0,
        le=24.0,
        description="Hours studied today (0–24)",
    )
    # Strict validation for input only
    topics: str = Field(min_length=1, max_length=500, description="Topics covered")
    reflection: str = Field(min_length=1, max_length=2000, description="Daily reflection")

class DailyLogCreate(DailyLogBase):
    tasks: List[TaskBase] = []

class DailyLogResponse(BaseModel):
    """Lenient schema for reading logs from DB — no min/max constraints so old records don't crash."""
    id: int
    user_id: int
    date: date
    xp_earned: int
    hours_studied: float = 0.0
    topics: Optional[str] = ""
    reflection: Optional[str] = ""

    class Config:
        from_attributes = True

class UserResponse(UserBase):
    id: int
    role: str
    streak: int
    longest_streak: int
    total_xp: int
    last_seen: Optional[datetime] = None
    tasks: List[TaskResponse] = []
    logs: List[DailyLogResponse] = []

    class Config:
        from_attributes = True

class FriendAdd(BaseModel):
    friend_email: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

class WeeklyWinnerResponse(BaseModel):
    id: int
    user_id: int
    winner_name: str
    week_start: date
    total_xp: int
    tasks_completed: int
    class Config:
        from_attributes = True
