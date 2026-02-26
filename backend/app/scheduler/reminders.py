"""Reminder scheduler — morning/evening check-ins."""
import logging
from datetime import date, datetime
from sqlalchemy import select

from app.database import async_session, User, ReminderSettings, UserStreak, DailyTask
from app.bot.i18n import t

logger = logging.getLogger(__name__)

# Will be set by main.py at startup
_bot = None

def set_bot(bot):
    global _bot
    _bot = bot


async def send_morning_reminders():
    """Send morning reminders to all users with enabled reminders."""
    if not _bot:
        return

    current_hour = datetime.utcnow().hour

    async with async_session() as session:
        result = await session.execute(
            select(ReminderSettings, User)
            .join(User, User.id == ReminderSettings.user_id)
            .where(ReminderSettings.enabled == True, User.is_active == True)
        )
        rows = result.all()

    for reminder, user in rows:
        # Simple hour check (could be more precise with timezone)
        morning_hour = int(reminder.morning_time.split(":")[0]) if reminder.morning_time else 8
        if current_hour != morning_hour:
            continue

        try:
            # Generate daily tasks
            from app.services.accountability import generate_daily_tasks
            await generate_daily_tasks(user.id)

            text = t("reminder_morning", user.language)
            # Add today's tasks summary
            tasks_result = await _get_today_tasks(user.id)
            for task_info in tasks_result:
                emoji = "[ ]"
                text += f"{emoji} {task_info}\n"

            await _bot.send_message(user.telegram_id, text)
        except Exception as e:
            logger.error(f"Morning reminder failed for user {user.telegram_id}: {e}")


async def send_evening_reminders():
    """Send evening check-in to all users."""
    if not _bot:
        return

    current_hour = datetime.utcnow().hour

    async with async_session() as session:
        result = await session.execute(
            select(ReminderSettings, User)
            .join(User, User.id == ReminderSettings.user_id)
            .where(ReminderSettings.enabled == True, User.is_active == True)
        )
        rows = result.all()

    for reminder, user in rows:
        evening_hour = int(reminder.evening_time.split(":")[0]) if reminder.evening_time else 21
        if current_hour != evening_hour:
            continue

        try:
            from app.services.accountability import check_daily_completion
            completion = await check_daily_completion(user.id)

            text = t("reminder_evening", user.language)
            if completion["all_done"]:
                text += {"en": "Great job today! All tasks completed!", "ru": "Отличная работа сегодня! Все задачи выполнены!"}.get(user.language, "Great job!")
            else:
                done = completion["completed_tasks"]
                total = completion["total_tasks"]
                text += {"en": f"Progress: {done}/{total} tasks done.", "ru": f"Прогресс: {done}/{total} задач выполнено."}.get(user.language, f"{done}/{total}")

            await _bot.send_message(user.telegram_id, text)

            # Update streak
            from app.services.accountability import update_streak
            await update_streak(user.id)

        except Exception as e:
            logger.error(f"Evening reminder failed for user {user.telegram_id}: {e}")


async def _get_today_tasks(user_id: int) -> list[str]:
    """Get task descriptions for today."""
    today = date.today()
    async with async_session() as session:
        result = await session.execute(
            select(DailyTask).where(DailyTask.user_id == user_id, DailyTask.date == today)
        )
        tasks = result.scalars().all()
    return [task.description or task.task_type for task in tasks]
