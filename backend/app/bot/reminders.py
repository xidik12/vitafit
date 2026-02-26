"""Bot reminder/task inline handlers."""
from aiogram import Router, F
from aiogram.types import CallbackQuery
from datetime import datetime
from sqlalchemy import select

from app.database import async_session, DailyTask

router = Router()


@router.callback_query(F.data.startswith("task_done:"))
async def on_task_done(callback: CallbackQuery):
    """Mark a task as completed via inline button."""
    task_id = int(callback.data.split(":")[1])
    await callback.answer()

    async with async_session() as session:
        result = await session.execute(
            select(DailyTask).where(DailyTask.id == task_id)
        )
        task = result.scalar_one_or_none()
        if task and not task.is_completed:
            task.is_completed = True
            task.completed_at = datetime.utcnow()
            await session.commit()
            await callback.message.edit_text(
                f"✅ {task.description or task.task_type}",
            )
        elif task and task.is_completed:
            await callback.message.edit_text(
                f"✅ {task.description or task.task_type} (already done)",
            )
