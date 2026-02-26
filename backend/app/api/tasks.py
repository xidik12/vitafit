"""Daily tasks API — exercise/meal/water task tracking."""
from datetime import date as dt_date, datetime
from fastapi import APIRouter, Depends
from sqlalchemy import select

from app.database import async_session, User, DailyTask
from app.dependencies import get_current_user

router = APIRouter(prefix="/api/tasks", tags=["tasks"])


@router.get("")
async def get_tasks(
    date: str | None = None,
    user: User = Depends(get_current_user),
):
    target_date = dt_date.fromisoformat(date) if date else dt_date.today()
    async with async_session() as session:
        result = await session.execute(
            select(DailyTask).where(
                DailyTask.user_id == user.id,
                DailyTask.date == target_date,
            )
        )
        tasks = result.scalars().all()

    return [
        {
            "id": t.id,
            "task_type": t.task_type,
            "description": t.description,
            "is_completed": t.is_completed,
            "completed_at": t.completed_at.isoformat() if t.completed_at else None,
        }
        for t in tasks
    ]


@router.post("/{task_id}/complete")
async def complete_task(task_id: int, user: User = Depends(get_current_user)):
    async with async_session() as session:
        result = await session.execute(
            select(DailyTask).where(
                DailyTask.id == task_id,
                DailyTask.user_id == user.id,
            )
        )
        task = result.scalar_one_or_none()
        if not task:
            return {"error": "Task not found"}

        task.is_completed = True
        task.completed_at = datetime.utcnow()
        await session.commit()

    return {"status": "ok"}
