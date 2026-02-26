"""Accountability service — streaks, XP, levels."""
import logging
from datetime import date, timedelta
from sqlalchemy import select, func

from app.database import async_session, User, UserStreak, Achievement, DailyTask, CalorieLog, WaterLog

logger = logging.getLogger(__name__)

# XP rewards
XP_EXERCISE_COMPLETE = 20
XP_MEAL_LOGGED = 10
XP_WATER_GOAL = 15
XP_WEIGHT_LOGGED = 10
XP_STREAK_BONUS = 5  # per day of streak
XP_PER_LEVEL = 100


async def check_daily_completion(user_id: int) -> dict:
    """Check if user completed all tasks for today. Returns completion stats."""
    today = date.today()
    async with async_session() as session:
        # Check tasks
        result = await session.execute(
            select(DailyTask).where(DailyTask.user_id == user_id, DailyTask.date == today)
        )
        tasks = result.scalars().all()
        total_tasks = len(tasks)
        completed_tasks = sum(1 for t in tasks if t.is_completed)

        # Check food logging
        food_result = await session.execute(
            select(func.count(CalorieLog.id)).where(
                CalorieLog.user_id == user_id, CalorieLog.date == today
            )
        )
        food_logged = food_result.scalar() > 0

        # Check water
        water_result = await session.execute(
            select(func.coalesce(func.sum(WaterLog.amount_ml), 0)).where(
                WaterLog.user_id == user_id, WaterLog.date == today
            )
        )
        water_total = water_result.scalar()

    return {
        "total_tasks": total_tasks,
        "completed_tasks": completed_tasks,
        "food_logged": food_logged,
        "water_ml": water_total,
        "all_done": completed_tasks == total_tasks and total_tasks > 0 and food_logged,
    }


async def update_streak(user_id: int):
    """Update user's streak based on today's activity."""
    today = date.today()
    yesterday = today - timedelta(days=1)

    async with async_session() as session:
        result = await session.execute(
            select(UserStreak).where(UserStreak.user_id == user_id)
        )
        streak = result.scalar_one_or_none()
        if not streak:
            streak = UserStreak(user_id=user_id)
            session.add(streak)

        completion = await check_daily_completion(user_id)

        if completion["all_done"]:
            if streak.last_active_date == yesterday:
                streak.current_streak += 1
            elif streak.last_active_date != today:
                streak.current_streak = 1

            streak.last_active_date = today

            if streak.current_streak > streak.longest_streak:
                streak.longest_streak = streak.current_streak

            # Award XP
            xp_earned = XP_EXERCISE_COMPLETE + XP_MEAL_LOGGED
            if completion["water_ml"] > 0:
                xp_earned += XP_WATER_GOAL
            xp_earned += XP_STREAK_BONUS * streak.current_streak
            streak.xp_total += xp_earned

            # Level up check
            new_level = (streak.xp_total // XP_PER_LEVEL) + 1
            if new_level > streak.level:
                streak.level = new_level
                # Award level-up achievement
                ach = Achievement(user_id=user_id, achievement_type=f"level_{new_level}")
                session.add(ach)

            # Streak milestones
            milestone_days = {3, 7, 14, 30, 60, 100, 365}
            if streak.current_streak in milestone_days:
                ach = Achievement(user_id=user_id, achievement_type=f"streak_{streak.current_streak}")
                session.add(ach)

        elif streak.last_active_date and streak.last_active_date < yesterday:
            # Missed a day — check skip mercy
            if not streak.skip_used_this_week:
                streak.skip_used_this_week = True
                # Don't break streak, mercy skip
            else:
                streak.current_streak = 0

        await session.commit()

    return streak


async def reset_weekly_skip():
    """Reset skip_used_this_week for all users (run on Monday)."""
    async with async_session() as session:
        from sqlalchemy import update
        await session.execute(
            update(UserStreak).values(skip_used_this_week=False)
        )
        await session.commit()
    logger.info("Weekly skip reset complete")


async def generate_daily_tasks(user_id: int):
    """Generate daily tasks based on user's current exercise/meal plan."""
    today = date.today()

    async with async_session() as session:
        # Check if tasks already exist for today
        existing = await session.execute(
            select(DailyTask).where(DailyTask.user_id == user_id, DailyTask.date == today).limit(1)
        )
        if existing.scalar_one_or_none():
            return  # Already generated

        # Create basic daily tasks
        tasks = [
            DailyTask(user_id=user_id, date=today, task_type="exercise", description="Complete today's workout"),
            DailyTask(user_id=user_id, date=today, task_type="meal", description="Log all meals"),
            DailyTask(user_id=user_id, date=today, task_type="water", description="Drink your water goal"),
        ]
        session.add_all(tasks)
        await session.commit()
