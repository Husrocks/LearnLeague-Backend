from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Boolean, Date
from sqlalchemy.orm import relationship
from datetime import datetime, date, timezone
from .database import Base

class Friendship(Base):
    __tablename__ = "friendships"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    friend_id = Column(Integer, ForeignKey("users.id"))

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    role = Column(String, default="user") # 'admin' or 'user'
    
    # Gamification Stats
    streak = Column(Integer, default=0)
    longest_streak = Column(Integer, default=0)
    total_xp = Column(Integer, default=0)
    learning_goal = Column(String, default="General")
    
    # Presence
    last_seen = Column(DateTime, nullable=True)
    
    # Relationships
    logs = relationship("DailyLog", back_populates="user")
    tasks = relationship("Task", back_populates="user")
    
    # Self-referential relationship for friends
    friends = relationship(
        "User", 
        secondary="friendships",
        primaryjoin=id==Friendship.user_id,
        secondaryjoin=id==Friendship.friend_id
    )

class DailyLog(Base):
    __tablename__ = "daily_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    date = Column(Date, default=lambda: datetime.now(timezone.utc).date())
    
    hours_studied = Column(Float, default=0.0)
    topics = Column(String)
    reflection = Column(String)
    
    xp_earned = Column(Integer, default=0)
    
    user = relationship("User", back_populates="logs")

class Task(Base):
    __tablename__ = "tasks"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    title = Column(String)
    status = Column(String, default="pending") # pending, completed, reviewed
    assigned_by = Column(String, nullable=True)
    date_assigned = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="tasks")

class WeeklyWinner(Base):
    __tablename__ = "weekly_winners"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    week_start = Column(Date, nullable=False)  # Monday of the winning week
    total_xp = Column(Integer, nullable=False)
    tasks_completed = Column(Integer, default=0)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    user = relationship("User")
