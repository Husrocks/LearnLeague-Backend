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
    password: str

class UserResponse(UserBase):
    id: int
    role: str
    streak: int
    longest_streak: int
    total_xp: int
    tasks: List[TaskResponse] = []

    class Config:
        from_attributes = True

class DailyLogBase(BaseModel):
    hours_studied: float
    topics: str
    reflection: str

class DailyLogCreate(DailyLogBase):
    tasks: List[TaskBase] = []

class DailyLogResponse(DailyLogBase):
    id: int
    user_id: int
    date: date
    xp_earned: int

    class Config:
        from_attributes = True

class FriendAdd(BaseModel):
    friend_email: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
