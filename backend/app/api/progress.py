"""Progress API — weight trends, streaks, achievements."""
from datetime import date as dt_date
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select

from app.database import async_session, User, WeightLog, UserStreak, Achievement
from app.dependencies import get_current_user

router = APIRouter(prefix="/api/progress", tags=["progress"])


class WeightLogRequest(BaseModel):
    weight_kg: float


@router.post("/weight")
async def log_weight(req: WeightLogRequest, user: User = Depends(get_current_user)):
    async with async_session() as session:
        log = WeightLog(user_id=user.id, date=dt_date.today(), weight_kg=req.weight_kg)
        session.add(log)
        await session.commit()
    return {"status": "ok"}


@router.get("/weight")
async def get_weight_history(
    limit: int = 30,
    user: User = Depends(get_current_user),
):
    async with async_session() as session:
        result = await session.execute(
            select(WeightLog)
            .where(WeightLog.user_id == user.id)
            .order_by(WeightLog.date.desc())
            .limit(limit)
        )
        logs = result.scalars().all()

    return [
        {"date": l.date.isoformat(), "weight_kg": l.weight_kg}
        for l in reversed(logs)
    ]


@router.get("/streak")
async def get_streak(user: User = Depends(get_current_user)):
    async with async_session() as session:
        result = await session.execute(
            select(UserStreak).where(UserStreak.user_id == user.id)
        )
        streak = result.scalar_one_or_none()

    if not streak:
        return {"current_streak": 0, "longest_streak": 0, "xp_total": 0, "level": 1}

    return {
        "current_streak": streak.current_streak,
        "longest_streak": streak.longest_streak,
        "xp_total": streak.xp_total,
        "level": streak.level,
        "last_active": streak.last_active_date.isoformat() if streak.last_active_date else None,
    }


@router.get("/achievements")
async def get_achievements(user: User = Depends(get_current_user)):
    async with async_session() as session:
        result = await session.execute(
            select(Achievement)
            .where(Achievement.user_id == user.id)
            .order_by(Achievement.earned_at.desc())
        )
        achievements = result.scalars().all()

    return [
        {"type": a.achievement_type, "earned_at": a.earned_at.isoformat()}
        for a in achievements
    ]
