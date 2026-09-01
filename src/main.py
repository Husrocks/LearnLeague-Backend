from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database import engine, Base
from .routers import auth, daily, social, test, tasks, cron, winner

# Create tables and seed initial data if empty
Base.metadata.create_all(bind=engine)

from .database import SessionLocal
from .models import User, Task
from .security import hash_password

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
            db.add(admin)
            db.commit()
    except Exception:
        db.rollback()
    finally:
        db.close()

seed_dev_data()

app = FastAPI(title="LearnLeague API")

import os
from urllib.parse import urlparse

# Configure CORS for Next.js frontend
raw_frontend_url = os.environ.get("FRONTEND_URL", "https://learn-league-platform.vercel.app")
parsed = urlparse(raw_frontend_url)
frontend_url = f"{parsed.scheme}://{parsed.netloc}" if parsed.netloc else raw_frontend_url.rstrip("/")

origins = [
    frontend_url,
    "http://localhost:3000",
    "https://learn-league-platform.vercel.app"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

import logging, uuid
from fastapi import Request

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s"
)
logger = logging.getLogger("learnleague")

@app.middleware("http")
async def log_requests(request: Request, call_next):
    request_id = request.headers.get("x-request-id", str(uuid.uuid4()))
    logger.info({"event": "request_start", "method": request.method,
                 "path": request.url.path, "rid": request_id})
    response = await call_next(request)
    logger.info({"event": "request_end", "status": response.status_code, "rid": request_id})
    response.headers["x-request-id"] = request_id
    return response

import traceback
from fastapi.responses import JSONResponse

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    # Log it locally
    logger.error(f"Global exception: {exc}")
    logger.error(traceback.format_exc())
    # Return details in HTTP response for debugging
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal Server Error", "error_message": str(exc), "traceback": traceback.format_exc()}
    )


app.include_router(auth.router)
app.include_router(daily.router)
app.include_router(social.router)
app.include_router(test.router)
app.include_router(tasks.router)
app.include_router(cron.router)
app.include_router(winner.router)

@app.get("/")
def read_root():
    return {"message": "Welcome to the LearnLeague Backend API"}
