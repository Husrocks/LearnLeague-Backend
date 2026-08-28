import os
from datetime import date, timedelta
from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import and_
from ..database import get_db
from ..models import User, DailyLog
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/cron", tags=["cron"])

CRON_SECRET = os.environ.get("CRON_SECRET", "")

def verify_cron(authorization: str = Header(None)):
    """Validates that the request comes from Vercel Cron (via Authorization header)."""
    if not CRON_SECRET or authorization != f"Bearer {CRON_SECRET}":
        raise HTTPException(status_code=403, detail="Unauthorized cron caller")

@router.post("/streaks")
def run_streak_monitor(db: Session = Depends(get_db), _=Depends(verify_cron)):
    yesterday = date.today() - timedelta(days=1)
    users_to_reset = (
        db.query(User)
        .outerjoin(DailyLog, and_(
            DailyLog.user_id == User.id,
            DailyLog.date == yesterday
        ))
        .filter(User.streak > 0, DailyLog.id == None)
        .all()
    )
    for u in users_to_reset:
        u.streak = 0
    if users_to_reset:
        db.commit()
    logger.info({"event": "streak_monitor", "reset_count": len(users_to_reset)})
    return {"reset": len(users_to_reset)}

@router.post("/weekly-winner")
def run_weekly_winner(db: Session = Depends(get_db), _=Depends(verify_cron)):
    # Find the Monday of the current week
    today = date.today()
    week_start = today - timedelta(days=today.weekday())

    # Calculate weekly XP from DailyLogs for this week
    from sqlalchemy import func
    from ..models import Task
    from ..models import WeeklyWinner
    weekly_xp = (
        db.query(DailyLog.user_id, func.sum(DailyLog.xp_earned).label("weekly_xp"))
        .filter(DailyLog.date >= week_start)
        .group_by(DailyLog.user_id)
        .order_by(func.sum(DailyLog.xp_earned).desc())
        .first()
    )
    if not weekly_xp:
        return {"winner": None, "message": "No activity this week"}

    winner_user_id, winner_xp = weekly_xp
    tasks_done = db.query(Task).filter(
        Task.user_id == winner_user_id,
        Task.status.in_(["completed", "reviewed"])
    ).count()

    winner_row = WeeklyWinner(
        user_id=winner_user_id,
        week_start=week_start,
        total_xp=int(winner_xp),
        tasks_completed=tasks_done
    )
    db.add(winner_row)
    db.commit()

    winner_name = db.query(User.name).filter(User.id == winner_user_id).scalar()
    logger.info({"event": "weekly_winner", "winner": winner_name, "xp": winner_xp})
    return {"winner": winner_name, "xp": int(winner_xp)}
