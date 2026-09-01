from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from ..database import get_db
from ..models import User, Task
from ..schemas import UserResponse, AdminTaskResponse, RoleUpdate
from ..dependencies import get_current_user

router = APIRouter(prefix="/admin", tags=["admin"])

def require_admin(current_user: User):
    if getattr(current_user, "role", None) != "admin":
        raise HTTPException(status_code=403, detail="Admin privileges required")

@router.get("/users", response_model=List[UserResponse])
def get_all_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_admin(current_user)
    users = db.query(User).all()
    return users

@router.get("/tasks", response_model=List[AdminTaskResponse])
def get_all_pending_tasks(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_admin(current_user)
    tasks = db.query(Task).filter(Task.status == "completed").all()
    
    # We need to map username and name from the user to the task
    response_tasks = []
    for task in tasks:
        admin_task = {
            "id": task.id,
            "user_id": task.user_id,
            "title": task.title,
            "status": task.status,
            "assigned_by": task.assigned_by,
            "date_assigned": task.date_assigned,
            "username": task.user.username if task.user else "Unknown",
            "name": task.user.name if task.user else "Unknown",
        }
        response_tasks.append(admin_task)
    
    return response_tasks

@router.put("/users/{target_user_id}/role", response_model=UserResponse)
def update_user_role(
    target_user_id: int,
    payload: RoleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_admin(current_user)
    
    # Don't let admin demote themselves (basic safety)
    if target_user_id == current_user.id and payload.role != "admin":
        raise HTTPException(status_code=400, detail="Cannot demote yourself")
        
    user = db.query(User).filter(User.id == target_user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    user.role = payload.role
    db.commit()
    db.refresh(user)
    return user
