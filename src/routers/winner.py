from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import User, WeeklyWinner
from ..schemas import WeeklyWinnerResponse
from ..dependencies import get_current_user

router = APIRouter(prefix="/winner", tags=["winner"])

@router.get("/current", response_model=WeeklyWinnerResponse)
def get_current_winner(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    winner_row = db.query(WeeklyWinner).order_by(WeeklyWinner.created_at.desc()).first()
    if not winner_row:
        raise HTTPException(status_code=404, detail="No weekly winner recorded yet")
    return {
        **winner_row.__dict__,
        "winner_name": winner_row.user.name
    }
