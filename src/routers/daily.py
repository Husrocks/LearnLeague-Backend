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

    # Prevent double-logging error, append instead
    today = date.today()
    existing_log = db.query(DailyLog).filter(
        DailyLog.user_id == user_id, DailyLog.date == today
    ).first()

    # XP Calculation Engine: 10 XP per hour + 5 XP per completed task
    tasks_done = sum(1 for t in log_data.tasks if t.status == "completed")
    xp_earned = int((log_data.hours_studied * 10) + (tasks_done * 5))

    if existing_log:
        existing_log.hours_studied += log_data.hours_studied
        if log_data.topics:
            existing_log.topics = f"{existing_log.topics}, {log_data.topics}" if existing_log.topics else log_data.topics
        if log_data.reflection:
            existing_log.reflection = f"{existing_log.reflection}\n{log_data.reflection}" if existing_log.reflection else log_data.reflection
        existing_log.xp_earned += xp_earned
        new_log = existing_log
    else:
        new_log = DailyLog(
            user_id=user_id,
            date=today,
            hours_studied=log_data.hours_studied,
            topics=log_data.topics,
            reflection=log_data.reflection,
            xp_earned=xp_earned,
        )
        db.add(new_log)
        
        # Streak Engine: increment if yesterday was logged, reset to 1 otherwise
        yesterday = today - timedelta(days=1)
        yesterday_log = db.query(DailyLog).filter(
            DailyLog.user_id == user_id, DailyLog.date == yesterday
        ).first()

        user.streak = (user.streak + 1) if yesterday_log else 1
        if user.streak > user.longest_streak:
            user.longest_streak = user.streak

    # Persist each task submitted with the log
    for task_data in log_data.tasks:
        new_task = Task(
            user_id=user_id,
            title=task_data.title,
            status=task_data.status,
        )
        db.add(new_task)

    user.total_xp += xp_earned

    db.commit()
    db.refresh(new_log)
    return new_log
