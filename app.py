import os
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.database import engine, Base, SessionLocal
from src.routers import auth, daily, social, test, tasks, winner
from src.models import User, Task
from src.security import hash_password

# Initialize database tables
Base.metadata.create_all(bind=engine)

def seed_dev_data():
    db = SessionLocal()
    try:
        if db.query(User).count() == 0:
            admin = User(
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
            friend1 = User(
                id=2,
                name="Sarah Chen",
                username="sarah_c",
                email="sarah@example.com",
                role="user",
                streak=12,
                longest_streak=15,
                total_xp=3100,
                learning_goal="Distributed Systems & Rust",
                hashed_password=hash_password("password123"),
            )
            friend2 = User(
                id=3,
                name="Alex Rivera",
                username="alex_r",
                email="alex@example.com",
                role="user",
                streak=4,
                longest_streak=8,
                total_xp=1890,
                learning_goal="LLM Fine-Tuning & Prompt Engineering",
                hashed_password=hash_password("password123"),
            )
            db.add_all([admin, friend1, friend2])
            db.commit()
            
            # Add friendships
            admin.friends.append(friend1)
            admin.friends.append(friend2)
            friend1.friends.append(admin)
            friend2.friends.append(admin)
            
            # Add demo tasks
            t1 = Task(user_id=1, title="Read Attention Is All You Need paper", status="completed", assigned_by="Sarah Chen")
            t2 = Task(user_id=1, title="Implement FastAPI middleware rate limiter", status="pending", assigned_by="Local Admin")
            t3 = Task(user_id=1, title="Review Rust concurrency patterns", status="pending", assigned_by="Alex Rivera")
            db.add_all([t1, t2, t3])
            db.commit()
    except Exception as e:
        db.rollback()
    finally:
        db.close()

seed_dev_data()

frontend_url = os.environ.get("FRONTEND_URL", "https://learn-league-platform.vercel.app")

# ============================================================
# FastAPI app with all routes
# ============================================================
api = FastAPI(title="LearnLeague API")

api.add_middleware(
    CORSMiddleware,
    allow_origins=[
        frontend_url.rstrip("/"),
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "https://learn-league-platform.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

api.include_router(auth.router)
api.include_router(daily.router)
api.include_router(social.router)
api.include_router(test.router)
api.include_router(tasks.router)
api.include_router(winner.router)

@api.get("/api")
def read_root():
    return {"message": "Welcome to the LearnLeague Backend API"}

# Optional Gradio UI (for Hugging Face Spaces deployment)
try:
    import gradio as gr
    def health_check(query: str = ""):
        return "✅ LearnLeague API is running!"

    with gr.Blocks(title="LearnLeague API") as demo:
        gr.Markdown("# 🏆 LearnLeague API")
        gr.Markdown("Backend REST API. Visit `/docs` for full API reference.")
        inp = gr.Textbox(label="Health Check")
        out = gr.Textbox(label="Status")
        gr.Button("Check Status").click(fn=health_check, inputs=inp, outputs=out)

    demo.queue()
    app = gr.mount_gradio_app(api, demo, path="/ui")
except Exception:
    app = api

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
