"""Profile API — get/update user profile."""
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select

from app.database import async_session, User, UserProfile, UserStreak
from app.dependencies import get_current_user

router = APIRouter(prefix="/api/profile", tags=["profile"])


class ProfileResponse(BaseModel):
    user_id: int
    telegram_id: int
    username: str | None
    language: str
    onboarding_complete: bool
    weight_kg: float | None = None
    height_cm: float | None = None
    age: int | None = None
    sex: str | None = None
    activity_level: str | None = None
    goal: str | None = None
    bmr: float | None = None
    tdee: float | None = None
    target_calories: int | None = None
    target_protein: int | None = None
    target_carbs: int | None = None
    target_fat: int | None = None
    target_water_ml: int | None = None
    dietary_pref: str | None = None
    current_streak: int = 0
    xp_total: int = 0
    level: int = 1


@router.get("")
async def get_profile(user: User = Depends(get_current_user)):
    async with async_session() as session:
        # Get profile
        result = await session.execute(
            select(UserProfile).where(UserProfile.user_id == user.id)
        )
        profile = result.scalar_one_or_none()

        # Get streak
        result = await session.execute(
            select(UserStreak).where(UserStreak.user_id == user.id)
        )
        streak = result.scalar_one_or_none()

    resp = ProfileResponse(
        user_id=user.id,
        telegram_id=user.telegram_id,
        username=user.username,
        language=user.language,
        onboarding_complete=user.onboarding_complete,
    )

    if profile:
        resp.weight_kg = profile.weight_kg
        resp.height_cm = profile.height_cm
        resp.age = profile.age
        resp.sex = profile.sex
        resp.activity_level = profile.activity_level
        resp.goal = profile.goal
        resp.bmr = profile.bmr
        resp.tdee = profile.tdee
        resp.target_calories = profile.target_calories
        resp.target_protein = profile.target_protein
        resp.target_carbs = profile.target_carbs
        resp.target_fat = profile.target_fat
        resp.target_water_ml = profile.target_water_ml
        resp.dietary_pref = profile.dietary_pref

    if streak:
        resp.current_streak = streak.current_streak
        resp.xp_total = streak.xp_total
        resp.level = streak.level

    return resp


class ProfileUpdateRequest(BaseModel):
    language: str | None = None
    weight_kg: float | None = None
    goal: str | None = None
    dietary_pref: str | None = None


@router.put("")
async def update_profile(req: ProfileUpdateRequest, user: User = Depends(get_current_user)):
    async with async_session() as session:
        # Update user language
        result = await session.execute(select(User).where(User.id == user.id))
        db_user = result.scalar_one()
        if req.language:
            db_user.language = req.language

        # Update profile
        result = await session.execute(
            select(UserProfile).where(UserProfile.user_id == user.id)
        )
        profile = result.scalar_one_or_none()
        if profile:
            if req.weight_kg is not None:
                profile.weight_kg = req.weight_kg
            if req.goal is not None:
                profile.goal = req.goal
            if req.dietary_pref is not None:
                profile.dietary_pref = req.dietary_pref

        await session.commit()

    return {"status": "ok"}
