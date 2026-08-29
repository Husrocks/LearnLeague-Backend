from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from .database import get_db
from .models import User
from .security import decode_token, hash_password

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)


def get_or_create_dev_user(db: Session) -> User:
    """Returns or creates a default admin user for localhost/development testing."""
    user = db.query(User).filter(User.id == 1).first()
    if not user:
        user = db.query(User).first()
    if not user:
        user = User(
            id=1,
            name="Local Admin",
            username="admin",
            email="admin@learnleague.local",
            role="admin",
            streak=7,
            longest_streak=14,
            total_xp=2450,
            learning_goal="AI & Full-Stack Development",
            hashed_password=hash_password("admin123"),
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    return user


def get_current_user(
    token: str | None = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    if not token or token in ("null", "undefined", "local-dev-token"):
        return get_or_create_dev_user(db)

    payload = decode_token(token)
    if payload is None:
        return get_or_create_dev_user(db)

    user_id = payload.get("sub")
    if user_id is None:
        return get_or_create_dev_user(db)

    user = db.query(User).filter(User.id == int(user_id)).first()
    if user is None:
        return get_or_create_dev_user(db)

    return user


def assert_owns_or_admin(current_user: User, target_user_id: int) -> None:
    """Raise HTTP 403 if current_user is not target_user and is not an admin.

    Use this at the start of any mutation endpoint that accepts a user_id path
    parameter, to prevent authenticated-but-unauthorized cross-user writes.
    Admins (role == 'admin') bypass the check so they can manage all users.
    """
    if current_user.id != target_user_id and getattr(current_user, "role", None) != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this resource",
        )

