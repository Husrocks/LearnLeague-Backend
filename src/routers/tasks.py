from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Task, User
from ..schemas import TaskCreate, TaskResponse
from ..dependencies import get_current_user

router = APIRouter(prefix="/tasks", tags=["tasks"])

@router.post("/{user_id}/assign", response_model=TaskResponse)
def assign_task(user_id: int, task: TaskCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    db_task = Task(
        user_id=user_id,
        title=task.title,
        status="pending",
        assigned_by=task.assigned_by
    )
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task

@router.put("/{task_id}/complete", response_model=TaskResponse)
def complete_task(task_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    db_task = db.query(Task).filter(Task.id == task_id).first()
    if not db_task:
        raise HTTPException(status_code=404, detail="Task not found")
        
    db_task.status = "completed"
    db.commit()
    db.refresh(db_task)
    return db_task

@router.put("/{task_id}/review", response_model=TaskResponse)
def review_task(task_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    db_task = db.query(Task).filter(Task.id == task_id).first()
    if not db_task:
        raise HTTPException(status_code=404, detail="Task not found")
        
    db_task.status = "reviewed"
    db.commit()
    db.refresh(db_task)
    return db_task
