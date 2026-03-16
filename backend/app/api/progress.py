"""Progress API — weight trends, streaks, achievements, measurements."""
import math
from datetime import date as dt_date
from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select, func

from app.database import async_session, User, WeightLog, UserStreak, Achievement, CalorieLog, WaterLog, MeasurementLog, UserProfile, HealthCheckLog
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


class HealthCheckRequest(BaseModel):
    resting_heart_rate: Optional[int] = None
    bp_systolic: Optional[int] = None
    bp_diastolic: Optional[int] = None
    spo2_pct: Optional[float] = None
    blood_glucose_mmol: Optional[float] = None
    energy_level: Optional[int] = None
    mood: Optional[int] = None
    recovery_score: Optional[int] = None
    notes: Optional[str] = None


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

        # Fetch achievements
        ach_result = await session.execute(
            select(Achievement).where(Achievement.user_id == user.id)
        )
        achievements = [a.achievement_type for a in ach_result.scalars().all()]

        # Compute weekly compliance: days active this week / 7
        today = dt_date.today()
        week_start = today - __import__('datetime').timedelta(days=today.weekday())
        workout_days = await session.execute(
            select(func.count(func.distinct(CalorieLog.date)))
            .where(CalorieLog.user_id == user.id, CalorieLog.date >= week_start)
        )
        active_days = workout_days.scalar() or 0
        weekly_compliance = round((active_days / 7) * 100, 1)

    if not streak:
        return {
            "current_streak": 0, "longest_streak": 0, "xp_total": 0, "level": 1,
            "achievements": achievements, "weekly_compliance": weekly_compliance,
        }

    return {
        "current_streak": streak.current_streak,
        "longest_streak": streak.longest_streak,
        "xp_total": streak.xp_total,
        "level": streak.level,
        "last_active": streak.last_active_date.isoformat() if streak.last_active_date else None,
        "achievements": achievements,
        "weekly_compliance": weekly_compliance,
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


# ---------------------------------------------------------------------------
# Health Check — vitals tracking
# ---------------------------------------------------------------------------

def _compute_health_status(log: HealthCheckLog) -> dict:
    """Compute color-coded health status indicators from a health check log."""
    indicators = {}

    if log.resting_heart_rate is not None:
        hr = log.resting_heart_rate
        if hr < 60:
            indicators["heart_rate"] = {"status": "info", "label": "Low RHR"}
        elif hr <= 80:
            indicators["heart_rate"] = {"status": "good", "label": "Normal"}
        elif hr <= 100:
            indicators["heart_rate"] = {"status": "warning", "label": "Elevated"}
        else:
            indicators["heart_rate"] = {"status": "danger", "label": "High"}

    if log.bp_systolic is not None and log.bp_diastolic is not None:
        sys, dia = log.bp_systolic, log.bp_diastolic
        if sys < 90 or dia < 60:
            indicators["blood_pressure"] = {"status": "warning", "label": "Low"}
        elif sys <= 120 and dia <= 80:
            indicators["blood_pressure"] = {"status": "good", "label": "Normal"}
        elif sys <= 140 or dia <= 90:
            indicators["blood_pressure"] = {"status": "warning", "label": "Elevated"}
        else:
            indicators["blood_pressure"] = {"status": "danger", "label": "High"}

    if log.spo2_pct is not None:
        if log.spo2_pct >= 97:
            indicators["spo2"] = {"status": "good", "label": "Normal"}
        elif log.spo2_pct >= 95:
            indicators["spo2"] = {"status": "info", "label": "Acceptable"}
        elif log.spo2_pct >= 90:
            indicators["spo2"] = {"status": "warning", "label": "Low"}
        else:
            indicators["spo2"] = {"status": "danger", "label": "Critical"}

    if log.blood_glucose_mmol is not None:
        bg = log.blood_glucose_mmol
        if bg < 3.9:
            indicators["blood_glucose"] = {"status": "warning", "label": "Low"}
        elif bg <= 5.5:
            indicators["blood_glucose"] = {"status": "good", "label": "Normal"}
        elif bg <= 7.0:
            indicators["blood_glucose"] = {"status": "warning", "label": "Pre-diabetic"}
        else:
            indicators["blood_glucose"] = {"status": "danger", "label": "High"}

    if log.energy_level is not None:
        if log.energy_level >= 7:
            indicators["energy"] = {"status": "good", "label": "High"}
        elif log.energy_level >= 4:
            indicators["energy"] = {"status": "info", "label": "Moderate"}
        else:
            indicators["energy"] = {"status": "warning", "label": "Low"}

    return indicators


@router.post("/health-check")
async def log_health_check(req: HealthCheckRequest, user: User = Depends(get_current_user)):
    today = dt_date.today()
    async with async_session() as session:
        log = HealthCheckLog(
            user_id=user.id,
            date=today,
            resting_heart_rate=req.resting_heart_rate,
            bp_systolic=req.bp_systolic,
            bp_diastolic=req.bp_diastolic,
            spo2_pct=req.spo2_pct,
            blood_glucose_mmol=req.blood_glucose_mmol,
            energy_level=req.energy_level,
            mood=req.mood,
            recovery_score=req.recovery_score,
            notes=req.notes,
        )
        session.add(log)

        # Update denormalized latest vitals on UserProfile
        profile_result = await session.execute(
            select(UserProfile).where(UserProfile.user_id == user.id)
        )
        profile = profile_result.scalar_one_or_none()
        if profile:
            if req.resting_heart_rate is not None:
                profile.latest_resting_hr = req.resting_heart_rate
            if req.bp_systolic is not None:
                profile.latest_bp_systolic = req.bp_systolic
            if req.bp_diastolic is not None:
                profile.latest_bp_diastolic = req.bp_diastolic
            if req.blood_glucose_mmol is not None:
                profile.latest_blood_glucose = req.blood_glucose_mmol

        await session.commit()
        await session.refresh(log)

    # Compute health status flags
    status = _compute_health_status(log)

    return {
        "id": log.id,
        "date": log.date.isoformat(),
        "resting_heart_rate": log.resting_heart_rate,
        "bp_systolic": log.bp_systolic,
        "bp_diastolic": log.bp_diastolic,
        "spo2_pct": log.spo2_pct,
        "blood_glucose_mmol": log.blood_glucose_mmol,
        "energy_level": log.energy_level,
        "mood": log.mood,
        "recovery_score": log.recovery_score,
        "notes": log.notes,
        "status": status,
    }


@router.get("/health-check")
async def get_health_checks(
    limit: int = 30,
    user: User = Depends(get_current_user),
):
    async with async_session() as session:
        result = await session.execute(
            select(HealthCheckLog)
            .where(HealthCheckLog.user_id == user.id)
            .order_by(HealthCheckLog.date.desc())
            .limit(limit)
        )
        logs = result.scalars().all()

    return [
        {
            "id": l.id,
            "date": l.date.isoformat(),
            "resting_heart_rate": l.resting_heart_rate,
            "bp_systolic": l.bp_systolic,
            "bp_diastolic": l.bp_diastolic,
            "spo2_pct": l.spo2_pct,
            "blood_glucose_mmol": l.blood_glucose_mmol,
            "energy_level": l.energy_level,
            "mood": l.mood,
            "recovery_score": l.recovery_score,
            "notes": l.notes,
        }
        for l in reversed(logs)
    ]


@router.get("/health-status")
async def get_health_status(user: User = Depends(get_current_user)):
    """Get latest health check with status indicators (green/yellow/red)."""
    async with async_session() as session:
        result = await session.execute(
            select(HealthCheckLog)
            .where(HealthCheckLog.user_id == user.id)
            .order_by(HealthCheckLog.date.desc())
            .limit(1)
        )
        latest = result.scalar_one_or_none()

    if not latest:
        return {"status": "no_data"}

    return {
        "date": latest.date.isoformat(),
        "resting_heart_rate": latest.resting_heart_rate,
        "bp_systolic": latest.bp_systolic,
        "bp_diastolic": latest.bp_diastolic,
        "spo2_pct": latest.spo2_pct,
        "blood_glucose_mmol": latest.blood_glucose_mmol,
        "energy_level": latest.energy_level,
        "mood": latest.mood,
        "recovery_score": latest.recovery_score,
        "indicators": _compute_health_status(latest),
    }
