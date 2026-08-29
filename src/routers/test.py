from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional
from sqlalchemy.orm import Session
from datetime import date, timedelta
import os
from ..database import get_db
from ..models import User, DailyLog, Task
from ..services.ai import (
    generate_assigned_topic_quiz, 
    generate_weekly_questions, 
    evaluate_answer
)
from ..dependencies import get_current_user

router = APIRouter(prefix="/test", tags=["test"])

@router.get("/debug-env")
def debug_env(current_user: User = Depends(get_current_user)):
    """Diagnostic endpoint — admin only."""
    if getattr(current_user, "role", None) != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    return {
        "has_db_url": "DATABASE_URL" in os.environ,
        "db_url_starts_with": os.environ.get("DATABASE_URL", "")[:15] if "DATABASE_URL" in os.environ else None,
        "has_secret": "SECRET_KEY" in os.environ,
    }

@router.get("/db-test")
def db_test(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """DB connectivity check — admin only."""
    if getattr(current_user, "role", None) != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    try:
        from sqlalchemy import text
        db.execute(text("SELECT 1"))
        return {"status": "success"}
    except Exception as e:
        import traceback
        return {"status": "error", "error": str(e), "traceback": traceback.format_exc()}

@router.get("/db-tables")
def db_tables(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Schema inspection — admin only."""
    if getattr(current_user, "role", None) != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    try:
        from sqlalchemy import text
        result = db.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema='public'"))
        tables = [row[0] for row in result]

        users_count = -1
        if 'users' in tables:
            users_count = db.execute(text("SELECT COUNT(*) FROM users")).scalar()

        return {"status": "success", "tables": tables, "users_count": users_count}
    except Exception as e:
        import traceback
        return {"status": "error", "error": str(e), "traceback": traceback.format_exc()}


class AnswerSubmit(BaseModel):
    question: str
    answer: str

class MCQEvaluationRequest(BaseModel):
    question_id: Optional[int] = 1
    topic: Optional[str] = "General"
    question: str
    selected_option: str
    correct_option: str
    explanation: Optional[str] = ""
    user_reasoning: Optional[str] = ""


@router.get("/{user_id}/generate")
def generate_test(
    user_id: int, 
    custom_topic: Optional[str] = Query(None, description="Optional custom topic to generate test on demand"),
    count: int = Query(3, ge=1, le=10, description="Number of questions to generate"),
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    """
    Dynamically generates on-demand questions with options based on the topics 
    assigned to the user by admin, tasks, and learning goals.
    """
    topics_list = []
    
    # 1. Check if user requested a specific on-demand topic
    if custom_topic and custom_topic.strip():
        topics_list.append(custom_topic.strip())
    
    # 2. Extract tasks assigned to the user (admin-assigned tasks)
    assigned_tasks = db.query(Task).filter(Task.user_id == user_id).all()
    for task in assigned_tasks:
        if task.title and task.title.strip() and task.title.strip() not in topics_list:
            topics_list.append(task.title.strip())

    # 3. Extract user learning goal
    user = db.query(User).filter(User.id == user_id).first()
    if user and user.learning_goal and user.learning_goal not in ("General", ""):
        if user.learning_goal not in topics_list:
            topics_list.append(user.learning_goal)

    # 4. Extract recent daily logs topics
    two_weeks_ago = date.today() - timedelta(days=14)
    logs = db.query(DailyLog).filter(
        DailyLog.user_id == user_id, 
        DailyLog.date >= two_weeks_ago
    ).all()
    for log in logs:
        if log.topics:
            for t in log.topics.split(","):
                clean_t = t.strip()
                if clean_t and clean_t not in topics_list:
                    topics_list.append(clean_t)

    # If still empty, use defaults
    if not topics_list:
        topics_list = [
            "FastAPI middleware rate limiter",
            "Attention Is All You Need & Transformer Architectures",
            "Distributed Systems Consistency and Concurrency"
        ]

    # Call Groq AI to generate on-demand quiz based on these assigned topics
    quiz_data = generate_assigned_topic_quiz(topics_list, count=count)
    questions = quiz_data.get("questions", [])

    # Format backwards-compatible single question string if needed
    first_q_formatted = ""
    if questions:
        first_q = questions[0]
        opt_lines = "\n".join([f"{o['id']}) {o['text']}" for o in first_q.get("options", [])])
        first_q_formatted = f"[{first_q.get('topic')}]\n{first_q.get('question')}\n\nOptions:\n{opt_lines}"

    return {
        "topics_covered": ", ".join(topics_list),
        "assigned_topics": topics_list,
        "questions": questions,
        "question": first_q_formatted,
        "model_used": quiz_data.get("model_used", "Groq LLM")
    }


@router.post("/{user_id}/evaluate-mcq")
def submit_mcq_answer(
    user_id: int, 
    payload: MCQEvaluationRequest, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    """
    Evaluates a multiple-choice question option selected by the user,
    provides architectural rationale, calculates score, and awards XP.
    """
    is_correct = payload.selected_option.strip().upper() == payload.correct_option.strip().upper()
    
    if is_correct:
        score = 100
        xp_earned = 25
        feedback_header = "🎉 Excellent! Correct choice."
    else:
        score = 30
        xp_earned = 5
        feedback_header = f"❌ Incorrect. The correct answer is Option {payload.correct_option}."

    explanation = payload.explanation or "The selected option addresses the architectural requirements most effectively."
    
    # If user provided additional reasoning, evaluate with AI for extra depth
    ai_reasoning_feedback = ""
    if payload.user_reasoning and len(payload.user_reasoning.strip()) > 5:
        try:
            ai_eval = evaluate_answer(payload.question, payload.user_reasoning)
            ai_reasoning_feedback = f"\n\nAI Review of your rationale: {ai_eval.get('feedback', '')}"
            if is_correct and ai_eval.get("score", 0) > 80:
                xp_earned += 10
        except Exception:
            pass

    # Award XP to user in database
    user = db.query(User).filter(User.id == user_id).first()
    if user:
        user.total_xp += xp_earned
        db.commit()

    full_feedback = f"{feedback_header}\n\nRationale:\n{explanation}{ai_reasoning_feedback}"

    return {
        "is_correct": is_correct,
        "score": score,
        "xp_earned": xp_earned,
        "selected_option": payload.selected_option,
        "correct_option": payload.correct_option,
        "feedback": full_feedback,
        "explanation": explanation,
        "follow_up": f"How would you optimize '{payload.topic}' under 10x traffic increase?"
    }


@router.post("/{user_id}/evaluate")
def submit_answer(user_id: int, payload: AnswerSubmit, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # 1. Call Groq AI to evaluate
    evaluation = evaluate_answer(payload.question, payload.answer)
    
    # 2. Update Gamification Engine
    # Give XP based on the score (e.g. 1 XP per score point)
    user = db.query(User).filter(User.id == user_id).first()
    if user:
        user.total_xp += int(evaluation.get("score", 0))
        db.commit()

    return evaluation
