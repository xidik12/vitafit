import jwt
from datetime import datetime, timedelta
from app.config import settings


def create_token(telegram_id: int) -> str:
    payload = {
        "sub": str(telegram_id),
        "exp": datetime.utcnow() + timedelta(hours=settings.jwt_expire_hours),
        "iat": datetime.utcnow(),
    }
    return jwt.encode(payload, settings.jwt_secret_key or "dev-secret", algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> dict | None:
    try:
        return jwt.decode(token, settings.jwt_secret_key or "dev-secret", algorithms=[settings.jwt_algorithm])
    except jwt.PyJWTError:
        return None
