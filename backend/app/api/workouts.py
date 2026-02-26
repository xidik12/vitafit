"""Workout Session API — start, log sets, finish, history, today."""
from datetime import date as dt_date, datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select, func

from app.database import (
    async_session,
    User,
    UserProfile,
    WorkoutSession,
    WorkoutSetLog,
    UserStreak,
    Achievement,
)
from app.dependencies import get_current_user

router = APIRouter(prefix="/api/workouts", tags=["workouts"])

# MET values by exercise type
MET_VALUES = {
    "strength": 5.0,
    "cardio": 8.0,
    "flexibility": 3.0,
    "yoga": 3.0,
    "tai_chi": 3.0,
}
MET_DEFAULT = 4.0

# XP awarded per completed workout
WORKOUT_XP = 30
XP_PER_LEVEL = 100


# ---------------------------------------------------------------------------
# Request schemas
# ---------------------------------------------------------------------------

class StartSessionRequest(BaseModel):
    plan_day_index: int


class LogSetRequest(BaseModel):
    exercise_name: str
    set_number: int
    reps_planned: Optional[int] = None
    reps_done: Optional[int] = None
    weight_kg: Optional[float] = None
    duration_secs: Optional[int] = None
    completed: bool = False


# ---------------------------------------------------------------------------
# Helper utilities
# ---------------------------------------------------------------------------

def _session_to_dict(s: WorkoutSession) -> dict:
    return {
        "id": s.id,
        "user_id": s.user_id,
        "date": s.date.isoformat(),
        "plan_day_index": s.plan_day_index,
        "started_at": s.started_at.isoformat() if s.started_at else None,
        "ended_at": s.ended_at.isoformat() if s.ended_at else None,
        "completed": s.completed,
        "calories_burned": s.calories_burned,
        "notes": s.notes,
        "duration_mins": s.duration_mins,
    }


def _set_log_to_dict(sl: WorkoutSetLog) -> dict:
    return {
        "id": sl.id,
        "session_id": sl.session_id,
        "exercise_name": sl.exercise_name,
        "set_number": sl.set_number,
        "reps_planned": sl.reps_planned,
        "reps_done": sl.reps_done,
        "weight_kg": sl.weight_kg,
        "duration_secs": sl.duration_secs,
        "completed": sl.completed,
    }


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/start")
async def start_workout_session(
    req: StartSessionRequest,
    user: User = Depends(get_current_user),
):
    """Start a new workout session for the given plan day index."""
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    today = dt_date.today()

    async with async_session() as session:
        workout = WorkoutSession(
            user_id=user.id,
            date=today,
            plan_day_index=req.plan_day_index,
            started_at=now,
            completed=False,
        )
        session.add(workout)
        await session.commit()
        await session.refresh(workout)

    return _session_to_dict(workout)


@router.post("/{session_id}/log-set")
async def log_set(
    session_id: int,
    req: LogSetRequest,
    user: User = Depends(get_current_user),
):
    """Log a completed set within a workout session."""
    async with async_session() as session:
        # Validate session belongs to user
        result = await session.execute(
            select(WorkoutSession).where(
                WorkoutSession.id == session_id,
                WorkoutSession.user_id == user.id,
            )
        )
        workout = result.scalar_one_or_none()
        if not workout:
            raise HTTPException(status_code=404, detail="Workout session not found")

        set_log = WorkoutSetLog(
            session_id=session_id,
            exercise_name=req.exercise_name,
            set_number=req.set_number,
            reps_planned=req.reps_planned,
            reps_done=req.reps_done,
            weight_kg=req.weight_kg,
            duration_secs=req.duration_secs,
            completed=req.completed,
        )
        session.add(set_log)
        await session.commit()
        await session.refresh(set_log)

    return _set_log_to_dict(set_log)


@router.post("/{session_id}/finish")
async def finish_workout_session(
    session_id: int,
    user: User = Depends(get_current_user),
):
    """Finish a workout session: calculate duration, calories, award XP, check achievements."""
    now = datetime.now(timezone.utc).replace(tzinfo=None)

    async with async_session() as session:
        # Fetch and validate the workout session
        result = await session.execute(
            select(WorkoutSession).where(
                WorkoutSession.id == session_id,
                WorkoutSession.user_id == user.id,
            )
        )
        workout = result.scalar_one_or_none()
        if not workout:
            raise HTTPException(status_code=404, detail="Workout session not found")

        # Calculate duration
        started = workout.started_at
        duration_secs = (now - started).total_seconds()
        duration_mins = max(1, int(duration_secs / 60))
        duration_hours = duration_mins / 60

        # Fetch user profile for weight
        profile_result = await session.execute(
            select(UserProfile).where(UserProfile.user_id == user.id)
        )
        profile = profile_result.scalar_one_or_none()
        weight_kg = profile.weight_kg if profile and profile.weight_kg else 70.0

        # Estimate calories using simple MET formula: MET * weight_kg * duration_hours
        # Using average MET of 5.0 (midpoint between strength and default)
        avg_met = 5.0
        calories_burned = round(avg_met * weight_kg * duration_hours, 1)

        # Mark session completed
        workout.ended_at = now
        workout.completed = True
        workout.duration_mins = duration_mins
        workout.calories_burned = calories_burned
        session.add(workout)

        # Award XP — get or create UserStreak
        streak_result = await session.execute(
            select(UserStreak).where(UserStreak.user_id == user.id)
        )
        streak = streak_result.scalar_one_or_none()
        if not streak:
            streak = UserStreak(user_id=user.id, xp_total=0, level=1)
            session.add(streak)

        streak.xp_total += WORKOUT_XP
        new_level = max(1, streak.xp_total // XP_PER_LEVEL + 1)
        leveled_up = new_level > streak.level
        streak.level = new_level
        streak.last_active_date = dt_date.today()
        session.add(streak)

        # Check "workout_10" achievement
        completed_count_result = await session.execute(
            select(func.count(WorkoutSession.id)).where(
                WorkoutSession.user_id == user.id,
                WorkoutSession.completed == True,
            )
        )
        completed_count = completed_count_result.scalar() or 0

        achievement_unlocked = None
        if completed_count >= 10:
            existing_ach = await session.execute(
                select(Achievement).where(
                    Achievement.user_id == user.id,
                    Achievement.achievement_type == "workout_10",
                )
            )
            if not existing_ach.scalar_one_or_none():
                ach = Achievement(user_id=user.id, achievement_type="workout_10")
                session.add(ach)
                achievement_unlocked = "workout_10"

        await session.commit()
        await session.refresh(workout)
        await session.refresh(streak)

    return {
        "session": _session_to_dict(workout),
        "xp_awarded": WORKOUT_XP,
        "xp_total": streak.xp_total,
        "level": streak.level,
        "leveled_up": leveled_up,
        "achievement_unlocked": achievement_unlocked,
        "completed_sessions": completed_count,
    }


@router.get("/history")
async def get_workout_history(
    limit: int = 20,
    user: User = Depends(get_current_user),
):
    """Return past workout sessions with set counts, ordered by date descending."""
    async with async_session() as session:
        sessions_result = await session.execute(
            select(WorkoutSession)
            .where(WorkoutSession.user_id == user.id)
            .order_by(WorkoutSession.date.desc(), WorkoutSession.started_at.desc())
            .limit(limit)
        )
        sessions = sessions_result.scalars().all()

        if not sessions:
            return []

        session_ids = [s.id for s in sessions]

        # Count sets per session in a single query
        sets_count_result = await session.execute(
            select(WorkoutSetLog.session_id, func.count(WorkoutSetLog.id).label("set_count"))
            .where(WorkoutSetLog.session_id.in_(session_ids))
            .group_by(WorkoutSetLog.session_id)
        )
        sets_by_session = {row.session_id: row.set_count for row in sets_count_result}

    return [
        {
            **_session_to_dict(s),
            "set_count": sets_by_session.get(s.id, 0),
        }
        for s in sessions
    ]


@router.get("/today")
async def get_today_session(user: User = Depends(get_current_user)):
    """Return the most recent workout session for today, or null if none exists."""
    today = dt_date.today()

    async with async_session() as session:
        result = await session.execute(
            select(WorkoutSession)
            .where(
                WorkoutSession.user_id == user.id,
                WorkoutSession.date == today,
            )
            .order_by(WorkoutSession.started_at.desc())
            .limit(1)
        )
        workout = result.scalar_one_or_none()

    if not workout:
        return {"session": None}

    return {"session": _session_to_dict(workout)}
