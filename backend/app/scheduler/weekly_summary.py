"""Weekly summary — sends Sunday compliance report."""
import logging
from datetime import date, timedelta
from sqlalchemy import select, func

from app.database import async_session, User, UserStreak, DailyTask, WeightLog, CalorieLog, WorkoutSession, UserProfile
from app.bot.i18n import t

logger = logging.getLogger(__name__)
_bot = None

def set_bot(bot):
    global _bot
    _bot = bot


async def send_weekly_summaries():
    """Send weekly summary to all active users on Sunday."""
    if not _bot:
        return

    today = date.today()
    week_start = today - timedelta(days=7)

    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.is_active == True, User.onboarding_complete == True)
        )
        users = result.scalars().all()

    for user in users:
        try:
            async with async_session() as session:
                # Tasks compliance
                total_tasks = await session.execute(
                    select(func.count(DailyTask.id)).where(
                        DailyTask.user_id == user.id,
                        DailyTask.date >= week_start,
                        DailyTask.date <= today,
                    )
                )
                completed_tasks = await session.execute(
                    select(func.count(DailyTask.id)).where(
                        DailyTask.user_id == user.id,
                        DailyTask.date >= week_start,
                        DailyTask.date <= today,
                        DailyTask.is_completed == True,
                    )
                )
                total = total_tasks.scalar() or 0
                done = completed_tasks.scalar() or 0
                compliance = round(done / total * 100) if total > 0 else 0

                # Streak
                streak_result = await session.execute(
                    select(UserStreak).where(UserStreak.user_id == user.id)
                )
                streak = streak_result.scalar_one_or_none()

                # Weight trend
                weight_result = await session.execute(
                    select(WeightLog)
                    .where(WeightLog.user_id == user.id, WeightLog.date >= week_start)
                    .order_by(WeightLog.date)
                )
                weights = weight_result.scalars().all()

                # Workout completion
                workout_result = await session.execute(
                    select(func.count(WorkoutSession.id)).where(
                        WorkoutSession.user_id == user.id,
                        WorkoutSession.date >= week_start,
                        WorkoutSession.completed == True,
                    )
                )
                workouts_done = workout_result.scalar() or 0

            lang = user.language
            if lang == "ru":
                text = "📊 <b>Недельный отчёт</b>\n\n"
                text += f"Выполнение задач: {compliance}% ({done}/{total})\n"
                if streak:
                    text += f"Серия: {streak.current_streak} дней\n"
                    text += f"Уровень: {streak.level} ({streak.xp_total} ОП)\n"
                text += f"Тренировок выполнено: {workouts_done}\n"
                if weights:
                    first_w = weights[0].weight_kg
                    last_w = weights[-1].weight_kg
                    diff = last_w - first_w
                    arrow = "↓" if diff < 0 else "↑" if diff > 0 else "→"
                    text += f"Вес: {last_w:.1f} кг ({arrow}{abs(diff):.1f})\n"
                text += "\nТак держать! 💪"
            else:
                text = "📊 <b>Weekly Summary</b>\n\n"
                text += f"Task compliance: {compliance}% ({done}/{total})\n"
                if streak:
                    text += f"Streak: {streak.current_streak} days\n"
                    text += f"Level: {streak.level} ({streak.xp_total} XP)\n"
                text += f"Workouts completed: {workouts_done}\n"
                if weights:
                    first_w = weights[0].weight_kg
                    last_w = weights[-1].weight_kg
                    diff = last_w - first_w
                    arrow = "↓" if diff < 0 else "↑" if diff > 0 else "→"
                    text += f"Weight: {last_w:.1f} kg ({arrow}{abs(diff):.1f})\n"
                text += "\nKeep it up! 💪"

            await _bot.send_message(user.telegram_id, text, parse_mode="HTML")

        except Exception as e:
            logger.error(f"Weekly summary failed for user {user.telegram_id}: {e}")
