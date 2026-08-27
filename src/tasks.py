from .celery_app import celery_app
from .database import SessionLocal
from .models import User, DailyLog
from datetime import date, timedelta
import logging

logger = logging.getLogger(__name__)

@celery_app.task
def calculate_weekly_winner():
    """
    Finds the user with the most weekly XP, optionally stores a winner record,
    and then resets everyone's weekly score for the new week.
    """
    db = SessionLocal()
    try:
        # 1. Find winner (Mock implementation for now: user with highest total XP)
        # In a real app we would have a separate 'weekly_xp' column or calculate it from DailyLogs.
        winner = db.query(User).order_by(User.total_xp.desc()).first()
        if winner:
            logger.info(f"Weekly Winner: {winner.username} with {winner.total_xp} total XP")
            
            # Here we would typically write to a 'WeeklyWinner' table
            
            # 2. Reset weekly stats (if we tracked them explicitly on the User model)
            # e.g., db.query(User).update({User.weekly_score: 0})
            db.commit()
            return f"Winner: {winner.username}"
        return "No users found"
    finally:
        db.close()

@celery_app.task
def monitor_streaks():
    """
    Runs daily. Checks if a user missed logging a DailyLog yesterday.
    If they missed it, their streak resets to 0.
    """
    db = SessionLocal()
    try:
        yesterday = date.today() - timedelta(days=1)
        users = db.query(User).filter(User.streak > 0).all()
        
        broken_streaks = 0
        for user in users:
            # Check if they logged yesterday
            logged_yesterday = db.query(DailyLog).filter(
                DailyLog.user_id == user.id, 
                DailyLog.date == yesterday
            ).first()
            
            if not logged_yesterday:
                # Break the streak
                logger.info(f"Breaking streak for {user.username} (was {user.streak})")
                user.streak = 0
                broken_streaks += 1
                
        if broken_streaks > 0:
            db.commit()
            
        return f"Broken {broken_streaks} streaks."
    finally:
        db.close()
