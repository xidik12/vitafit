"""Questionnaire API — submit full questionnaire from mini-app."""
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select

from app.database import async_session, User, UserProfile, UserStreak, ReminderSettings, QuestionnaireAnswer
from app.dependencies import get_current_user

router = APIRouter(prefix="/api/questionnaire", tags=["questionnaire"])


@router.get("/answers")
async def get_answers(user: User = Depends(get_current_user)):
    async with async_session() as session:
        result = await session.execute(
            select(QuestionnaireAnswer).where(QuestionnaireAnswer.user_id == user.id)
        )
        answers = result.scalars().all()

    return [
        {
            "module": a.module,
            "question_key": a.question_key,
            "answer_value": a.answer_value,
        }
        for a in answers
    ]


class FullQuestionnaireSubmit(BaseModel):
    consent: bool = True
    parq: dict = {}
    goal: str = "health"
    age: int = 30
    gender: str | None = None
    height_cm: float = 170
    weight_kg: float = 70
    target_weight_kg: float | None = None
    diet_preference: str = "no_restriction"
    sleep_hours: float = 7
    sleep_quality: str = "good"
    activity_level: str = "moderate"
    stress_level: str = "moderate"
    work_type: str = "sedentary"


@router.post("/answers")
async def submit_questionnaire(req: FullQuestionnaireSubmit, user: User = Depends(get_current_user)):
    sex = req.gender or "male"
    weight = req.weight_kg
    height = req.height_cm
    age = req.age
    activity = req.activity_level
    goal = req.goal

    # Mifflin-St Jeor BMR
    if sex == "male":
        bmr = 10 * weight + 6.25 * height - 5 * age + 5
    else:
        bmr = 10 * weight + 6.25 * height - 5 * age - 161

    # Activity multiplier
    multipliers = {
        "sedentary": 1.2,
        "light": 1.375,
        "moderate": 1.55,
        "active": 1.725,
        "very_active": 1.9,
    }
    tdee = bmr * multipliers.get(activity, 1.55)

    # Adjust for goal
    if goal == "weight_loss":
        target_cals = int(tdee - 500)
    elif goal == "muscle":
        target_cals = int(tdee + 300)
    else:
        target_cals = int(tdee)

    # Macros
    target_protein = int(weight * 1.6)
    target_fat = int(target_cals * 0.25 / 9)
    target_carbs = int((target_cals - target_protein * 4 - target_fat * 9) / 4)
    target_water = int(weight * 33)

    # PAR-Q check
    parq_passed = not any(v == "yes" for v in req.parq.values())

    # Map diet preference
    diet_map = {"no_restriction": "none", "halal": "halal", "vegetarian": "vegetarian", "vegan": "vegan", "gluten_free": "none", "dairy_free": "none"}
    dietary_pref = diet_map.get(req.diet_preference, "none")

    async with async_session() as session:
        # Get fresh user
        result = await session.execute(select(User).where(User.id == user.id))
        db_user = result.scalar_one()

        # Check existing profile
        result = await session.execute(
            select(UserProfile).where(UserProfile.user_id == user.id)
        )
        profile = result.scalar_one_or_none()

        profile_data = dict(
            weight_kg=weight,
            height_cm=height,
            age=age,
            sex=sex,
            activity_level=activity,
            goal=goal,
            bmr=round(bmr, 1),
            tdee=round(tdee, 1),
            target_calories=target_cals,
            target_protein=target_protein,
            target_carbs=target_carbs,
            target_fat=target_fat,
            target_water_ml=target_water,
            parq_passed=parq_passed,
            dietary_pref=dietary_pref,
            job_type=req.work_type,
            stress_level=req.stress_level,
        )

        if profile:
            for k, v in profile_data.items():
                setattr(profile, k, v)
        else:
            profile = UserProfile(user_id=user.id, **profile_data)
            session.add(profile)

        # Create streak if not exists
        result = await session.execute(
            select(UserStreak).where(UserStreak.user_id == user.id)
        )
        if not result.scalar_one_or_none():
            session.add(UserStreak(user_id=user.id))

        # Create reminder settings if not exists
        result = await session.execute(
            select(ReminderSettings).where(ReminderSettings.user_id == user.id)
        )
        if not result.scalar_one_or_none():
            session.add(ReminderSettings(user_id=user.id))

        db_user.onboarding_complete = True
        db_user.consent_given = req.consent
        await session.commit()

    # Return profile for frontend
    return {
        "status": "ok",
        "profile": {
            "onboarding_complete": True,
            "weight_kg": weight,
            "height_cm": height,
            "age": age,
            "sex": sex,
            "goal": goal,
            "calorie_goal": target_cals,
            "water_goal_ml": target_water,
            "target_protein": target_protein,
            "target_carbs": target_carbs,
            "target_fat": target_fat,
            "dietary_pref": dietary_pref,
        },
    }
