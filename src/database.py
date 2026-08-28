import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Use DATABASE_URL from environment if available (e.g. for Supabase), otherwise use local SQLite
db_url = os.environ.get("DATABASE_URL")

# SQLAlchemy 1.4+ requires postgresql:// instead of postgres://
if db_url and db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)

if not db_url:
    # On serverless environments like Vercel, the root filesystem is read-only.
    # We must use /tmp for SQLite if no external database is provided.
    is_vercel = os.environ.get("VERCEL") == "1"
    sqlite_path = "/tmp/learnleague.db" if is_vercel else "./learnleague.db"
    db_url = f"sqlite:///{sqlite_path}"

SQLALCHEMY_DATABASE_URL = db_url

# If using Postgres, check_same_thread is invalid, so we only apply it to SQLite
connect_args = {"check_same_thread": False} if SQLALCHEMY_DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args=connect_args
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
