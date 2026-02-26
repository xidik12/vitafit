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


# ---------------------------------------------------------------------------
# GET /suggestions — Phase 2: progressive overload suggestions
# ---------------------------------------------------------------------------
@router.get("/suggestions", summary="Get progressive overload suggestions")
async def get_suggestions(user: User = Depends(get_current_user)):
    """
    Return progressive overload suggestions for the authenticated user based
    on their recent exercise history and current plan.
    """
    from app.services.exercise_planner import get_progression_suggestions
    suggestions = await get_progression_suggestions(user.id)
    return {"suggestions": suggestions}


# ---------------------------------------------------------------------------
# GET /substitutes — Phase 8/9: find substitute exercises
# ---------------------------------------------------------------------------
@router.get("/substitutes", summary="Find substitute exercises")
async def find_substitutes(
    name: str = Query(..., description="Exercise name to find substitutes for"),
    user: User = Depends(get_current_user),
):
    """
    Return up to 5 substitute exercises that target the same muscle group
    as the given exercise, with the same or lower difficulty level.

    Lookup is case-insensitive on the exercise name. Returns HTTP 404 if
    the original exercise cannot be found in the library.
    """
    # Difficulty ordering used to filter same-or-lower difficulty substitutes
    difficulty_order = {"beginner": 0, "intermediate": 1, "advanced": 2}

    async with async_session() as session:
        # Look up the original exercise by name (case-insensitive)
        result = await session.execute(
            select(Exercise).where(Exercise.name_en.ilike(name.strip()))
        )
        original = result.scalar_one_or_none()

        if not original:
            raise HTTPException(
                status_code=404,
                detail=f"Exercise '{name}' not found in the library.",
            )

        original_difficulty_rank = difficulty_order.get(
            (original.difficulty or "").lower(), 1
        )

        # Collect difficulty levels that are same or lower than original
        allowed_difficulties = [
            level
            for level, rank in difficulty_order.items()
            if rank <= original_difficulty_rank
        ]

        # Query substitutes: same target_muscle, same/lower difficulty, exclude original
        sub_query = (
            select(Exercise)
            .where(Exercise.target_muscle == original.target_muscle)
            .where(Exercise.difficulty.in_(allowed_difficulties))
            .where(Exercise.id != original.id)
            .limit(5)
        )
        sub_result = await session.execute(sub_query)
        substitutes = sub_result.scalars().all()

    return {
        "original": original.name_en,
        "target_muscle": original.target_muscle,
        "substitutes": [
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
            for e in substitutes
        ],
    }
