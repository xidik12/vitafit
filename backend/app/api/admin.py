"""Admin API — basic stats and management."""
from fastapi import APIRouter, HTTPException
from sqlalchemy import select, func

from app.config import settings
from app.database import async_session, User, CalorieLog, ExercisePlan

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.get("/stats")
async def get_stats(admin_id: int = 0):
    if admin_id != settings.admin_telegram_id:
        raise HTTPException(status_code=403, detail="Unauthorized")

    async with async_session() as session:
        users_count = await session.execute(select(func.count(User.id)))
        active_count = await session.execute(
            select(func.count(User.id)).where(User.onboarding_complete == True)
        )
        logs_count = await session.execute(select(func.count(CalorieLog.id)))
        plans_count = await session.execute(select(func.count(ExercisePlan.id)))

    return {
        "total_users": users_count.scalar(),
        "active_users": active_count.scalar(),
        "total_food_logs": logs_count.scalar(),
        "total_exercise_plans": plans_count.scalar(),
    }
