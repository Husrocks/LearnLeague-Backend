from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database import engine, Base
from .routers import auth, daily, social, test, tasks, cron, winner

# Create tables (In a real app, use Alembic)
Base.metadata.create_all(bind=engine)

app = FastAPI(title="LearnLeague API")

import os

# Configure CORS for Next.js frontend
frontend_url = os.environ.get("FRONTEND_URL", "https://learn-league-platform.vercel.app")
frontend_url = frontend_url.rstrip("/")  # Remove trailing slash if user added it accidentally

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins (development)
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
