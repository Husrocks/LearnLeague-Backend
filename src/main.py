from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database import engine, Base
from .routers import auth, daily, social, test, tasks

# Create tables (In a real app, use Alembic)
Base.metadata.create_all(bind=engine)

app = FastAPI(title="LearnLeague API")

import os

# Configure CORS for Next.js frontend
frontend_url = os.environ.get("FRONTEND_URL", "http://localhost:3000")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[frontend_url, "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(daily.router)
app.include_router(social.router)
app.include_router(test.router)
app.include_router(tasks.router)

@app.get("/")
def read_root():
    return {"message": "Welcome to the LearnLeague Backend API"}
