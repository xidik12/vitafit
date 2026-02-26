"""Calorie tracking API — food logging, search, daily summary."""
from datetime import date as dt_date
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import select, func

from app.database import async_session, User, CalorieLog, WaterLog, FoodItem, UserProfile
from app.dependencies import get_current_user
from app.services.food_search import search_food, get_by_barcode

router = APIRouter(prefix="/api/calories", tags=["calories"])


@router.get("/search")
async def search(
    q: str = Query(..., min_length=1),
    lang: str = "ru",
    limit: int = 20,
    user: User = Depends(get_current_user),
):
    results = await search_food(q, lang, limit)
    return {"results": results}


@router.get("/barcode/{barcode}")
async def barcode_lookup(barcode: str, user: User = Depends(get_current_user)):
    result = await get_by_barcode(barcode)
    if not result:
        return {"error": "Product not found"}
    return result


class FoodLogRequest(BaseModel):
    meal_type: str  # breakfast/lunch/dinner/snack
    food_id: int | None = None
    food_name: str | None = None
    amount_g: float
    calories: float
    protein: float | None = None
    carbs: float | None = None
    fat: float | None = None


@router.post("/log")
async def log_food(req: FoodLogRequest, user: User = Depends(get_current_user)):
    async with async_session() as session:
        log = CalorieLog(
            user_id=user.id,
            date=dt_date.today(),
            meal_type=req.meal_type,
            food_id=req.food_id,
            food_name_override=req.food_name,
            amount_g=req.amount_g,
            calories=req.calories,
            protein=req.protein,
            carbs=req.carbs,
            fat=req.fat,
        )
        session.add(log)
        await session.commit()
    return {"status": "ok"}


@router.delete("/log/{log_id}")
async def delete_log(log_id: int, user: User = Depends(get_current_user)):
    async with async_session() as session:
        result = await session.execute(
            select(CalorieLog).where(CalorieLog.id == log_id, CalorieLog.user_id == user.id)
        )
        log = result.scalar_one_or_none()
        if log:
            await session.delete(log)
            await session.commit()
    return {"status": "ok"}


@router.get("/daily")
async def daily_summary(
    date: str | None = None,
    user: User = Depends(get_current_user),
):
    target_date = dt_date.fromisoformat(date) if date else dt_date.today()

    async with async_session() as session:
        # Get food logs
        result = await session.execute(
            select(CalorieLog).where(
                CalorieLog.user_id == user.id,
                CalorieLog.date == target_date,
            ).order_by(CalorieLog.created_at)
        )
        logs = result.scalars().all()

        # Get water logs
        water_result = await session.execute(
            select(func.coalesce(func.sum(WaterLog.amount_ml), 0)).where(
                WaterLog.user_id == user.id,
                WaterLog.date == target_date,
            )
        )
        water_total = water_result.scalar()

        # Get targets
        profile_result = await session.execute(
            select(UserProfile).where(UserProfile.user_id == user.id)
        )
        profile = profile_result.scalar_one_or_none()

    # Calculate totals
    total_calories = sum(l.calories for l in logs)
    total_protein = sum(l.protein or 0 for l in logs)
    total_carbs = sum(l.carbs or 0 for l in logs)
    total_fat = sum(l.fat or 0 for l in logs)

    # Group by meal type
    meals = {}
    for log in logs:
        if log.meal_type not in meals:
            meals[log.meal_type] = []
        meals[log.meal_type].append({
            "id": log.id,
            "food_name": log.food_name_override or "Food",
            "amount_g": log.amount_g,
            "calories": log.calories,
            "protein": log.protein,
            "carbs": log.carbs,
            "fat": log.fat,
        })

    return {
        "date": target_date.isoformat(),
        "meals": meals,
        "totals": {
            "calories": round(total_calories),
            "protein": round(total_protein),
            "carbs": round(total_carbs),
            "fat": round(total_fat),
        },
        "targets": {
            "calories": profile.target_calories if profile else 2000,
            "protein": profile.target_protein if profile else 80,
            "carbs": profile.target_carbs if profile else 250,
            "fat": profile.target_fat if profile else 65,
            "water_ml": profile.target_water_ml if profile else 2300,
        },
        "water_ml": water_total,
    }


class WaterLogRequest(BaseModel):
    amount_ml: int = 250


@router.post("/water")
async def log_water(req: WaterLogRequest, user: User = Depends(get_current_user)):
    async with async_session() as session:
        log = WaterLog(user_id=user.id, date=dt_date.today(), amount_ml=req.amount_ml)
        session.add(log)
        await session.commit()
    return {"status": "ok"}
