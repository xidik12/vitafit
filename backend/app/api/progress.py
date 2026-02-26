"""Progress API — weight trends, streaks, achievements, measurements."""
import math
from datetime import date as dt_date
from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select, func

from app.database import async_session, User, WeightLog, UserStreak, Achievement, CalorieLog, WaterLog, MeasurementLog, UserProfile
from app.dependencies import get_current_user

router = APIRouter(prefix="/api/progress", tags=["progress"])


class WeightLogRequest(BaseModel):
    weight_kg: float


class MeasurementRequest(BaseModel):
    waist_cm: Optional[float] = None
    hips_cm: Optional[float] = None
    chest_cm: Optional[float] = None
    left_arm_cm: Optional[float] = None
    right_arm_cm: Optional[float] = None
    left_thigh_cm: Optional[float] = None
    right_thigh_cm: Optional[float] = None
    neck_cm: Optional[float] = None


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


@router.get("/today")
async def get_today_summary(user: User = Depends(get_current_user)):
    today = dt_date.today()

    async with async_session() as session:
        # Sum today's calories
        cal_result = await session.execute(
            select(func.coalesce(func.sum(CalorieLog.calories), 0))
            .where(CalorieLog.user_id == user.id, CalorieLog.date == today)
        )
        calories_consumed = cal_result.scalar()

        # Sum today's water intake
        water_result = await session.execute(
            select(func.coalesce(func.sum(WaterLog.amount_ml), 0))
            .where(WaterLog.user_id == user.id, WaterLog.date == today)
        )
        water_ml = water_result.scalar()

        # Get current streak
        streak_result = await session.execute(
            select(UserStreak).where(UserStreak.user_id == user.id)
        )
        streak = streak_result.scalar_one_or_none()

    return {
        "calories_consumed": int(calories_consumed),
        "water_ml": int(water_ml),
        "streak": streak.current_streak if streak else 0,
    }


# ---------------------------------------------------------------------------
# Phase 6: Body measurements
# ---------------------------------------------------------------------------
@router.post("/measurements")
async def log_measurement(req: MeasurementRequest, user: User = Depends(get_current_user)):
    today = dt_date.today()
    body_fat_pct = None

    # Auto-calculate body fat % using the US Navy method if sufficient data
    if req.neck_cm and req.waist_cm:
        async with async_session() as session:
            result = await session.execute(
                select(UserProfile).where(UserProfile.user_id == user.id)
            )
            profile = result.scalar_one_or_none()

        if profile and profile.height_cm:
            height = profile.height_cm
            waist = req.waist_cm
            neck = req.neck_cm
            sex = (profile.sex or "male").lower()

            try:
                if sex == "female" and req.hips_cm:
                    hips = req.hips_cm
                    body_fat_pct = round(
                        495 / (1.29579 - 0.35004 * math.log10(waist + hips - neck) + 0.22100 * math.log10(height)) - 450,
                        1,
                    )
                elif sex != "female":
                    body_fat_pct = round(
                        495 / (1.0324 - 0.19077 * math.log10(waist - neck) + 0.15456 * math.log10(height)) - 450,
                        1,
                    )
            except (ValueError, ZeroDivisionError):
                body_fat_pct = None

    async with async_session() as session:
        log = MeasurementLog(
            user_id=user.id,
            date=today,
            waist_cm=req.waist_cm,
            hips_cm=req.hips_cm,
            chest_cm=req.chest_cm,
            left_arm_cm=req.left_arm_cm,
            right_arm_cm=req.right_arm_cm,
            left_thigh_cm=req.left_thigh_cm,
            right_thigh_cm=req.right_thigh_cm,
            neck_cm=req.neck_cm,
            body_fat_pct=body_fat_pct,
        )
        session.add(log)
        await session.commit()
        await session.refresh(log)

    return {
        "id": log.id,
        "date": log.date.isoformat(),
        "waist_cm": log.waist_cm,
        "hips_cm": log.hips_cm,
        "chest_cm": log.chest_cm,
        "left_arm_cm": log.left_arm_cm,
        "right_arm_cm": log.right_arm_cm,
        "left_thigh_cm": log.left_thigh_cm,
        "right_thigh_cm": log.right_thigh_cm,
        "neck_cm": log.neck_cm,
        "body_fat_pct": log.body_fat_pct,
    }


@router.get("/measurements")
async def get_measurements(
    limit: int = 30,
    user: User = Depends(get_current_user),
):
    async with async_session() as session:
        result = await session.execute(
            select(MeasurementLog)
            .where(MeasurementLog.user_id == user.id)
            .order_by(MeasurementLog.date.desc())
            .limit(limit)
        )
        logs = result.scalars().all()

    return [
        {
            "id": l.id,
            "date": l.date.isoformat(),
            "waist_cm": l.waist_cm,
            "hips_cm": l.hips_cm,
            "chest_cm": l.chest_cm,
            "left_arm_cm": l.left_arm_cm,
            "right_arm_cm": l.right_arm_cm,
            "left_thigh_cm": l.left_thigh_cm,
            "right_thigh_cm": l.right_thigh_cm,
            "neck_cm": l.neck_cm,
            "body_fat_pct": l.body_fat_pct,
        }
        for l in reversed(logs)
    ]
