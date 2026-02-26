"""Auth API — Telegram WebApp authentication."""
import hashlib
import hmac
import json
import logging
from urllib.parse import parse_qs

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlalchemy import select

from app.config import settings
from app.database import async_session, User
from app.jwt_utils import create_token

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/auth", tags=["auth"])


class TelegramAuthRequest(BaseModel):
    init_data: str


@router.post("/telegram")
async def auth_telegram(req: TelegramAuthRequest):
    """Validate Telegram WebApp init data and return JWT."""
    if settings.debug:
        # In debug mode, accept any init_data
        parsed = parse_qs(req.init_data)
        user_json = parsed.get("user", [None])[0]
        if user_json:
            user_data = json.loads(user_json)
        else:
            # Fallback for testing
            user_data = {"id": 1, "first_name": "Dev", "username": "dev_user"}
    else:
        # Validate hash
        parsed = parse_qs(req.init_data)
        received_hash = parsed.pop("hash", [None])[0]
        if not received_hash:
            raise HTTPException(status_code=401, detail="Missing hash")

        # Build check string
        items = sorted(
            (k, v[0]) for k, v in parsed.items()
        )
        check_string = "\n".join(f"{k}={v}" for k, v in items)
        secret = hmac.new(
            b"WebAppData", settings.telegram_bot_token.encode(), hashlib.sha256
        ).digest()
        computed = hmac.new(secret, check_string.encode(), hashlib.sha256).hexdigest()

        if computed != received_hash:
            raise HTTPException(status_code=401, detail="Invalid hash")

        user_json = parsed.get("user", [None])[0]
        if not user_json:
            raise HTTPException(status_code=401, detail="No user data")
        user_data = json.loads(user_json)

    telegram_id = user_data["id"]

    async with async_session() as session:
        result = await session.execute(select(User).where(User.telegram_id == telegram_id))
        user = result.scalar_one_or_none()
        if not user:
            user = User(
                telegram_id=telegram_id,
                username=user_data.get("username"),
                first_name=user_data.get("first_name"),
                language=user_data.get("language_code", "ru")[:2],
            )
            session.add(user)
            await session.commit()
            await session.refresh(user)

    token = create_token(telegram_id)
    return {"token": token, "user_id": user.id}
