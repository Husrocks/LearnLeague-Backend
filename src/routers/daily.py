from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import date, timedelta
from ..database import get_db
from ..models import User, DailyLog, Task
from ..schemas import DailyLogCreate, DailyLogResponse
from ..dependencies import get_current_user

router = APIRouter(prefix="/learning", tags=["learning"])

@router.post("/{user_id}/log", response_model=DailyLogResponse)
def log_daily_learning(user_id: int, log_data: DailyLogCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    # Check if already logged today
    today = date.today()
    existing_log = db.query(DailyLog).filter(DailyLog.user_id == user_id, DailyLog.date == today).first()
    if existing_log:
        raise HTTPException(status_code=400, detail="Already logged learning for today")

    # XP Calculation Engine
    # 10 XP per hour studied + 5 XP per task completed
    tasks_done = sum(1 for t in log_data.tasks if t.done)
    xp_earned = int((log_data.hours_studied * 10) + (tasks_done * 5))

    new_log = DailyLog(
        user_id=user_id,
        date=today,
        hours_studied=log_data.hours_studied,
        topics=log_data.topics,
        reflection=log_data.reflection,
        xp_earned=xp_earned
    )
    db.add(new_log)
    
    # Add tasks
    for task_data in log_data.tasks:
        new_task = Task(user_id=user_id, label=task_data.label, done=task_data.done)
        db.add(new_task)

    # Streak Engine Calculation
    yesterday = today - timedelta(days=1)
    yesterday_log = db.query(DailyLog).filter(DailyLog.user_id == user_id, DailyLog.date == yesterday).first()
    
    if yesterday_log:
        user.streak += 1
    else:
        user.streak = 1 # Reset to 1 (first day of new streak)
        
    if user.streak > user.longest_streak:
        user.longest_streak = user.streak

    user.total_xp += xp_earned
    
    db.commit()
    db.refresh(new_log)
    
    return new_log
