from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import date, timedelta
from ..database import get_db
from ..models import User, DailyLog, Task
from ..schemas import DailyLogCreate, DailyLogResponse
from ..dependencies import get_current_user, assert_owns_or_admin

router = APIRouter(prefix="/learning", tags=["learning"])


@router.post("/{user_id}/log", response_model=DailyLogResponse)
def log_daily_learning(
    user_id: int,
    log_data: DailyLogCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # T4 fix: ownership check — users can only log for themselves (admins exempt)
    assert_owns_or_admin(current_user, user_id)

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Prevent double-logging on the same day
    today = date.today()
    existing_log = db.query(DailyLog).filter(
        DailyLog.user_id == user_id, DailyLog.date == today
    ).first()
    if existing_log:
        raise HTTPException(status_code=400, detail="Already logged learning for today")

    # XP Calculation Engine: 10 XP per hour + 5 XP per completed task
    # T4 fix: use .status == "completed" instead of the non-existent .done field
    tasks_done = sum(1 for t in log_data.tasks if t.status == "completed")
    xp_earned = int((log_data.hours_studied * 10) + (tasks_done * 5))

    new_log = DailyLog(
        user_id=user_id,
        date=today,
        hours_studied=log_data.hours_studied,
        topics=log_data.topics,
        reflection=log_data.reflection,
        xp_earned=xp_earned,
    )
    db.add(new_log)

    # Persist each task submitted with the log
    # T4 fix: use .title and .status instead of the non-existent .label and .done fields
    for task_data in log_data.tasks:
        new_task = Task(
            user_id=user_id,
            title=task_data.title,
            status=task_data.status,
        )
        db.add(new_task)

    # Streak Engine: increment if yesterday was logged, reset to 1 otherwise
    yesterday = today - timedelta(days=1)
    yesterday_log = db.query(DailyLog).filter(
        DailyLog.user_id == user_id, DailyLog.date == yesterday
    ).first()

    user.streak = (user.streak + 1) if yesterday_log else 1
    if user.streak > user.longest_streak:
        user.longest_streak = user.streak

    user.total_xp += xp_earned

    db.commit()
    db.refresh(new_log)
    return new_log
