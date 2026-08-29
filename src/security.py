import os
import sys
import logging
from datetime import datetime, timedelta
from passlib.context import CryptContext
from jose import JWTError, jwt

logger = logging.getLogger(__name__)

_IS_PROD = bool(
    os.environ.get("VERCEL")
    or os.environ.get("ENVIRONMENT", "").lower() == "production"
)
_SECRET_RAW = os.environ.get("SECRET_KEY", "")
_KNOWN_BAD = "CHANGE_THIS_IN_PRODUCTION_ENV"

if not _SECRET_RAW or _SECRET_RAW == _KNOWN_BAD:
    if _IS_PROD:
        sys.exit(
            "FATAL: SECRET_KEY is not set or is the insecure default. "
            "Set a strong SECRET_KEY environment variable in Vercel before deploying."
        )
    _SECRET_RAW = "dev-only-insecure-secret-do-not-use-in-production"
    logger.warning(
        "SECRET_KEY not set — using insecure dev default. "
        "This MUST be set via environment variable before production deployment."
    )

SECRET_KEY: str = _SECRET_RAW
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_SECONDS = 60 * 60 * 24 * 7  # 7 days

import bcrypt

def hash_password(plain: str) -> str:
    # bcrypt truncates at 72 bytes
    pwd_bytes = plain.encode("utf-8")[:72]
    return bcrypt.hashpw(pwd_bytes, bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    try:
        pwd_bytes = plain.encode("utf-8")[:72]
        return bcrypt.checkpw(pwd_bytes, hashed.encode("utf-8"))
    except Exception:
        return False


def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(seconds=ACCESS_TOKEN_EXPIRE_SECONDS)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> dict | None:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None
