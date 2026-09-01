from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import User
from ..schemas import UserCreate, UserResponse, TokenResponse, UserUpdate
from ..security import hash_password, verify_password, create_access_token
from ..dependencies import get_current_user

router = APIRouter(prefix="/auth", tags=["auth"])


from sqlalchemy import func

@router.post("/register", response_model=UserResponse, status_code=201)
def register(user: UserCreate, db: Session = Depends(get_db)):
    clean_email = user.email.strip().lower()
    clean_username = user.username.strip()

    if db.query(User).filter(func.lower(User.email) == clean_email).first():
        raise HTTPException(status_code=409, detail="Email already registered")
    if db.query(User).filter(func.lower(User.username) == clean_username.lower()).first():
        raise HTTPException(status_code=409, detail="Username already taken")

    new_user = User(
        name=user.name.strip(),
        username=clean_username,
        email=clean_email,
        hashed_password=hash_password(user.password),
        learning_goal=user.learning_goal,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


class LoginRequest(BaseModel):
    email: str
    password: str


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    clean_email = payload.email.strip().lower()
    user = db.query(User).filter(func.lower(User.email) == clean_email).first()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    token = create_access_token({"sub": str(user.id)})
    return TokenResponse(access_token=token, token_type="bearer", user=user)


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.patch("/me", response_model=UserResponse)
def update_me(
    payload: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if payload.name is not None:
        current_user.name = payload.name
    if payload.learning_goal is not None:
        current_user.learning_goal = payload.learning_goal

    db.commit()
    db.refresh(current_user)
    return current_user
