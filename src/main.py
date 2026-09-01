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

import os, logging, uuid, traceback
from urllib.parse import urlparse
from fastapi import Request
from fastapi.responses import JSONResponse

# ---------------------------------------------------------------------------
# CORS — must be added FIRST so it wraps everything (Starlette runs middleware
# in reverse order of registration, outermost = last added).
# ---------------------------------------------------------------------------
ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "https://learn-league-platform.vercel.app",
]
raw = os.environ.get("FRONTEND_URL", "")
if raw:
    parsed = urlparse(raw)
    clean = f"{parsed.scheme}://{parsed.netloc}" if parsed.netloc else raw.rstrip("/")
    if clean not in ALLOWED_ORIGINS:
        ALLOWED_ORIGINS.append(clean)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# ---------------------------------------------------------------------------
# Request logging middleware (runs INSIDE the CORS wrapper)
# ---------------------------------------------------------------------------
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

# ---------------------------------------------------------------------------
# Global exception handler
# ---------------------------------------------------------------------------
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global exception: {exc}")
    logger.error(traceback.format_exc())
    origin = request.headers.get("origin", "https://learn-league-platform.vercel.app")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal Server Error", "error_message": str(exc)},
        headers={
            "Access-Control-Allow-Origin": origin,
            "Access-Control-Allow-Credentials": "true",
        },
    )

# ---------------------------------------------------------------------------
# Explicit OPTIONS preflight catch-all (belt-and-suspenders for Vercel)
# ---------------------------------------------------------------------------
from fastapi.routing import APIRoute
from starlette.routing import Route
from starlette.responses import Response

@app.options("/{rest_of_path:path}")
async def preflight_handler(rest_of_path: str, request: Request):
    return Response(
        status_code=200,
        headers={
            "Access-Control-Allow-Origin": request.headers.get("origin", "*"),
            "Access-Control-Allow-Methods": "GET, POST, PUT, PATCH, DELETE, OPTIONS",
            "Access-Control-Allow-Headers": "Authorization, Content-Type, x-request-id",
            "Access-Control-Allow-Credentials": "true",
            "Access-Control-Max-Age": "86400",
        },
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
