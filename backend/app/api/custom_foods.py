"""Custom foods API — user-created foods and recent/frequent food lookups."""
import logging
import random
from datetime import date, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select, func, desc

from app.database import async_session, User, CustomFoodItem, CalorieLog, WeeklyChallenge
from app.dependencies import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/foods", tags=["foods"])


# --------------- Schemas ---------------

class CustomFoodCreate(BaseModel):
    name_en: str
    name_ru: str | None = None
    calories_per_100g: float
    protein_per_100g: float | None = None
    carbs_per_100g: float | None = None
    fat_per_100g: float | None = None


class CustomFoodOut(BaseModel):
    id: int
    name_en: str
    name_ru: str | None
    calories_per_100g: float | None
    protein_per_100g: float | None
    carbs_per_100g: float | None
    fat_per_100g: float | None

    class Config:
        from_attributes = True


class RecentFoodOut(BaseModel):
    name: str
    count: int
    calories: float | None
    protein: float | None
    carbs: float | None
    fat: float | None
    amount_g: float | None = None


class ChallengeOut(BaseModel):
    id: int
    week_start: date
    challenge_type: str
    target_value: int
    current_value: int
    completed: bool

    class Config:
        from_attributes = True


# --------------- Custom Foods ---------------

@router.post("/custom", response_model=CustomFoodOut)
async def create_custom_food(body: CustomFoodCreate, user: User = Depends(get_current_user)):
    """Create a custom food item for the current user."""
    async with async_session() as session:
        food = CustomFoodItem(
            user_id=user.id,
            name_en=body.name_en,
            name_ru=body.name_ru,
            calories_per_100g=body.calories_per_100g,
            protein_per_100g=body.protein_per_100g,
            carbs_per_100g=body.carbs_per_100g,
            fat_per_100g=body.fat_per_100g,
        )
        session.add(food)
        await session.commit()
        await session.refresh(food)
    return food


@router.get("/custom", response_model=list[CustomFoodOut])
async def list_custom_foods(user: User = Depends(get_current_user)):
    """List all custom foods for the current user, newest first."""
    async with async_session() as session:
        result = await session.execute(
            select(CustomFoodItem)
            .where(CustomFoodItem.user_id == user.id)
            .order_by(desc(CustomFoodItem.created_at))
        )
        foods = result.scalars().all()
    return foods


@router.delete("/custom/{food_id}")
async def delete_custom_food(food_id: int, user: User = Depends(get_current_user)):
    """Delete a custom food item (must belong to current user)."""
    async with async_session() as session:
        result = await session.execute(
            select(CustomFoodItem).where(
                CustomFoodItem.id == food_id,
                CustomFoodItem.user_id == user.id,
            )
        )
        food = result.scalar_one_or_none()
        if not food:
            raise HTTPException(status_code=404, detail="Custom food not found")
        await session.delete(food)
        await session.commit()
    return {"status": "ok"}


# --------------- Recent / Frequent Foods ---------------

@router.get("/recent", response_model=list[RecentFoodOut])
async def recent_foods(user: User = Depends(get_current_user)):
    """Return the user's top-10 most frequently logged foods."""
    async with async_session() as session:
        # Subquery: group by food name, count occurrences
        freq_q = (
            select(
                CalorieLog.food_name_override.label("name"),
                func.count(CalorieLog.id).label("cnt"),
                func.max(CalorieLog.id).label("latest_id"),
            )
            .where(
                CalorieLog.user_id == user.id,
                CalorieLog.food_name_override.isnot(None),
            )
            .group_by(CalorieLog.food_name_override)
            .order_by(desc("cnt"))
            .limit(10)
            .subquery()
        )

        # Join back to get nutrition from the most recent entry
        rows = await session.execute(
            select(
                freq_q.c.name,
                freq_q.c.cnt,
                CalorieLog.calories,
                CalorieLog.protein,
                CalorieLog.carbs,
                CalorieLog.fat,
                CalorieLog.amount_g,
            ).join(CalorieLog, CalorieLog.id == freq_q.c.latest_id)
        )
        results = rows.all()

    return [
        RecentFoodOut(
            name=row.name,
            count=row.cnt,
            calories=row.calories,
            protein=row.protein,
            carbs=row.carbs,
            fat=row.fat,
            amount_g=row.amount_g,
        )
        for row in results
    ]


# --------------- Weekly Challenge ---------------

_CHALLENGE_TYPES = [
    ("log_meals_5", 5),
    ("complete_workouts_4", 4),
    ("drink_water_7", 7),
    ("log_weight_5", 5),
]


def _most_recent_monday() -> date:
    today = date.today()
    return today - timedelta(days=today.weekday())


@router.get("/challenges", response_model=ChallengeOut)
async def get_current_challenge(user: User = Depends(get_current_user)):
    """Get this week's challenge, auto-generating one if none exists."""
    monday = _most_recent_monday()

    async with async_session() as session:
        result = await session.execute(
            select(WeeklyChallenge).where(
                WeeklyChallenge.user_id == user.id,
                WeeklyChallenge.week_start == monday,
            )
        )
        challenge = result.scalar_one_or_none()

        if not challenge:
            ctype, target = random.choice(_CHALLENGE_TYPES)
            challenge = WeeklyChallenge(
                user_id=user.id,
                week_start=monday,
                challenge_type=ctype,
                target_value=target,
                current_value=0,
                completed=False,
            )
            session.add(challenge)
            await session.commit()
            await session.refresh(challenge)

    return challenge
