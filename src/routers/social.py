from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from ..database import get_db
from ..models import User, Friendship
from ..schemas import UserResponse, FriendAdd
from ..dependencies import get_current_user

router = APIRouter(prefix="/social", tags=["social"])

@router.get("/leaderboard", response_model=List[UserResponse])
def get_leaderboard(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    users = db.query(User).order_by(User.total_xp.desc()).limit(50).all()
    return users

@router.get("/friends/{user_id}", response_model=List[UserResponse])
def get_friends(user_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return user.friends

@router.post("/friends/{user_id}/add", response_model=UserResponse)
def add_friend(user_id: int, payload: FriendAdd, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    user = db.query(User).filter(User.id == user_id).first()
    friend = db.query(User).filter(User.email == payload.friend_email).first()
    
    if not user or not friend:
        raise HTTPException(status_code=404, detail="User or friend not found")
        
    if friend in user.friends:
        raise HTTPException(status_code=400, detail="Already friends")
        
    # Create bidirectional friendship for simplicity
    user.friends.append(friend)
    friend.friends.append(user)
    db.commit()
    
    return friend

@router.delete("/friends/{user_id}/remove/{friend_id}")
def remove_friend(user_id: int, friend_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    user = db.query(User).filter(User.id == user_id).first()
    friend = db.query(User).filter(User.id == friend_id).first()
    
    if not user or not friend:
        raise HTTPException(status_code=404, detail="User or friend not found")
        
    if friend in user.friends:
        user.friends.remove(friend)
    if user in friend.friends:
        friend.friends.remove(user)
        
    db.commit()
    return {"status": "success"}
