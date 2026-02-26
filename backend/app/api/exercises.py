"""Exercise API — exercise plans and exercise library."""
import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func

from app.database import async_session, User, Exercise, ExercisePlan
from app.dependencies import get_current_user
from app.services.exercise_planner import generate_exercise_plan

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/exercises", tags=["exercises"])


# ---------------------------------------------------------------------------
# GET /plan — retrieve current (latest) exercise plan
# ---------------------------------------------------------------------------
@router.get("/plan", summary="Get current exercise plan")
async def get_exercise_plan(user: User = Depends(get_current_user)):
    """
    Return the most recently generated exercise plan for the authenticated user.

    The plan is identified by the highest week_number in the exercise_plans table.
    Returns a 404-style message if no plan exists yet.
    """
    async with async_session() as session:
        result = await session.execute(
            select(ExercisePlan)
            .where(ExercisePlan.user_id == user.id)
            .order_by(ExercisePlan.week_number.desc())
            .limit(1)
        )
        plan = result.scalar_one_or_none()

    if not plan:
        return {
            "plan": None,
            "week": None,
            "message": "No exercise plan found. Please complete your health questionnaire and generate a plan.",
        }

    return {
        "plan": plan.plan_json,
        "week": plan.week_number,
        "created_at": plan.created_at.isoformat() if plan.created_at else None,
    }


# ---------------------------------------------------------------------------
# POST /plan/generate — create a new exercise plan
# ---------------------------------------------------------------------------
@router.post("/plan/generate", summary="Generate a new exercise plan")
async def generate_plan(user: User = Depends(get_current_user)):
    """
    Generate and persist a fresh weekly exercise plan for the authenticated user.

    The plan is based on the user's profile (age, goal, PAR-Q result, activity
    level, available equipment, weekly time budget).

    Returns HTTP 400 if the user has not completed their profile yet.
    """
    try:
        plan = await generate_exercise_plan(user.id)
    except Exception as exc:
        logger.exception(f"Error generating exercise plan for user {user.id}: {exc}")
        raise HTTPException(status_code=500, detail="Failed to generate exercise plan")

    if plan is None:
        raise HTTPException(
            status_code=400,
            detail="Profile not found. Please complete the health questionnaire first.",
        )

    # Fetch week number from the plan dict itself
    week = plan.get("week_number")

    return {
        "plan": plan,
        "week": week,
        "message": "Exercise plan generated successfully.",
    }


# ---------------------------------------------------------------------------
# GET /library — browse exercise database
# ---------------------------------------------------------------------------
@router.get("/library", summary="Browse exercise library")
async def exercise_library(
    body_part: str | None = Query(
        default=None,
        description="Filter by body part (e.g. chest, back, legs, core, shoulders, arms)",
    ),
    exercise_type: str | None = Query(
        default=None,
        description="Filter by type (strength / cardio / flexibility / tai_chi / yoga)",
    ),
    difficulty: str | None = Query(
        default=None,
        description="Filter by difficulty (beginner / intermediate / advanced)",
    ),
    limit: int = Query(default=50, ge=1, le=200, description="Max records to return"),
    offset: int = Query(default=0, ge=0, description="Pagination offset"),
    user: User = Depends(get_current_user),
):
    """
    Browse the exercise database with optional filters.

    Supported filters (all optional, combinable):
    - body_part: partial case-insensitive match on the body_part column
    - exercise_type: exact match (strength / cardio / flexibility / tai_chi / yoga)
    - difficulty: exact match (beginner / intermediate / advanced)
    - limit / offset: pagination
    """
    async with async_session() as session:
        query = select(Exercise)

        if body_part:
            query = query.where(
                Exercise.body_part.ilike(f"%{body_part.strip()}%")
            )
        if exercise_type:
            query = query.where(Exercise.exercise_type == exercise_type.strip().lower())
        if difficulty:
            query = query.where(Exercise.difficulty == difficulty.strip().lower())

        # Total count for pagination metadata
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await session.execute(count_query)
        total = total_result.scalar_one()

        query = query.offset(offset).limit(limit)
        result = await session.execute(query)
        exercises = result.scalars().all()

    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "exercises": [
            {
                "id": e.id,
                "name_en": e.name_en,
                "name_ru": e.name_ru,
                "body_part": e.body_part,
                "target_muscle": e.target_muscle,
                "equipment": e.equipment,
                "difficulty": e.difficulty,
                "exercise_type": e.exercise_type,
                "instructions": e.instructions,
                "images": e.images,
                "source": e.source,
            }
            for e in exercises
        ],
    }
