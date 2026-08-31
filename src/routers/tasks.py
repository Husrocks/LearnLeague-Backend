from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import date, timedelta
from ..database import get_db
from ..models import Task, User, DailyLog
from ..schemas import TaskCreate, TaskResponse
from ..dependencies import get_current_user, assert_owns_or_admin

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.post("/{user_id}/assign", response_model=TaskResponse)
def assign_task(
    user_id: int,
    task: TaskCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # T5: users can only assign tasks to themselves; admins can assign to anyone
    assert_owns_or_admin(current_user, user_id)

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    db_task = Task(
        user_id=user_id,
        title=task.title,
        status="pending",
        assigned_by=task.assigned_by,
    )
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task


@router.put("/{task_id}/complete", response_model=TaskResponse)
def complete_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    db_task = db.query(Task).filter(Task.id == task_id).first()
    if not db_task:
        raise HTTPException(status_code=404, detail="Task not found")

    # T5: only the task owner (or an admin) can mark a task complete
    assert_owns_or_admin(current_user, db_task.user_id)

    db_task.status = "completed"
    db.commit()
    db.refresh(db_task)
    return db_task


@router.put("/{task_id}/review", response_model=TaskResponse)
def review_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    db_task = db.query(Task).filter(Task.id == task_id).first()
    if not db_task:
        raise HTTPException(status_code=404, detail="Task not found")

    # T5: only admins can review/approve tasks
    if getattr(current_user, "role", None) != "admin":
        raise HTTPException(
            status_code=403,
            detail="Only admins can approve task reviews",
        )

    db_task.status = "reviewed"
    
    # Award XP and update consistency streak
    task_user = db.query(User).filter(User.id == db_task.user_id).first()
    if task_user:
        task_user.total_xp += 10
        
        today = date.today()
        existing_log = db.query(DailyLog).filter(
            DailyLog.user_id == task_user.id, DailyLog.date == today
        ).first()
        
        if existing_log:
            existing_log.xp_earned += 10
        else:
            # First action of the day! Create log and update streak
            new_log = DailyLog(
                user_id=task_user.id,
                date=today,
                hours_studied=0.0,
                topics=f"Task Approved: {db_task.title}",
                reflection="",
                xp_earned=10,
            )
            db.add(new_log)
            
            yesterday = today - timedelta(days=1)
            yesterday_log = db.query(DailyLog).filter(
                DailyLog.user_id == task_user.id, DailyLog.date == yesterday
            ).first()

            task_user.streak = (task_user.streak + 1) if yesterday_log else 1
            if task_user.streak > task_user.longest_streak:
                task_user.longest_streak = task_user.streak

    db.commit()
    db.refresh(db_task)
    return db_task

@router.put("/{task_id}/reject", response_model=TaskResponse)
def reject_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    db_task = db.query(Task).filter(Task.id == task_id).first()
    if not db_task:
        raise HTTPException(status_code=404, detail="Task not found")

    if getattr(current_user, "role", None) != "admin":
        raise HTTPException(
            status_code=403,
            detail="Only admins can reject task reviews",
        )

    db_task.status = "pending"
    db.commit()
    db.refresh(db_task)
    return db_task
