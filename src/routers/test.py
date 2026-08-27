from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from datetime import date, timedelta
from ..database import get_db
from ..models import User, DailyLog
from ..services.ai import generate_weekly_questions, evaluate_answer

router = APIRouter(prefix="/test", tags=["test"])

class AnswerSubmit(BaseModel):
    question: str
    answer: str

@router.get("/{user_id}/generate")
def generate_test(user_id: int, db: Session = Depends(get_db)):
    # 1. Fetch user's logs for the past 7 days
    seven_days_ago = date.today() - timedelta(days=7)
    logs = db.query(DailyLog).filter(
        DailyLog.user_id == user_id, 
        DailyLog.date >= seven_days_ago
    ).all()
    
    if not logs:
        # Default topic if no logs
        topics = "General Software Engineering"
    else:
        # 2. Extract topics studied
        topics = ", ".join([log.topics for log in logs if log.topics])

    # 3. Call Groq AI to generate a question
    question = generate_weekly_questions(topics)
    
    return {"question": question, "topics_covered": topics}

@router.post("/{user_id}/evaluate")
def submit_answer(user_id: int, payload: AnswerSubmit, db: Session = Depends(get_db)):
    # 1. Call Groq AI to evaluate
    evaluation = evaluate_answer(payload.question, payload.answer)
    
    # 2. Update Gamification Engine
    # Give XP based on the score (e.g. 1 XP per score point)
    user = db.query(User).filter(User.id == user_id).first()
    if user:
        user.total_xp += int(evaluation.get("score", 0))
        db.commit()

    return evaluation
