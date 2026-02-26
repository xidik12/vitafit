"""Recipe API — meal plans and recipe database."""
import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func

from app.database import async_session, User, Recipe, RecipeIngredient, MealPlan
from app.dependencies import get_current_user
from app.services.meal_planner import generate_meal_plan

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/recipes", tags=["recipes"])


# ---------------------------------------------------------------------------
# GET /plan — retrieve current (latest) meal plan
# ---------------------------------------------------------------------------
@router.get("/plan", summary="Get current meal plan")
async def get_meal_plan(user: User = Depends(get_current_user)):
    """
    Return the most recently generated meal plan for the authenticated user.

    The plan is identified by the highest week_number in the meal_plans table.
    Returns a message if no plan exists yet.
    """
    async with async_session() as session:
        result = await session.execute(
            select(MealPlan)
            .where(MealPlan.user_id == user.id)
            .order_by(MealPlan.week_number.desc())
            .limit(1)
        )
        plan = result.scalar_one_or_none()

    if not plan:
        return {
            "plan": None,
            "week": None,
            "message": "No meal plan found. Please complete your health questionnaire and generate a plan.",
        }

    return {
        "plan": plan.plan_json,
        "week": plan.week_number,
        "created_at": plan.created_at.isoformat() if plan.created_at else None,
    }


# ---------------------------------------------------------------------------
# POST /plan/generate — create a new meal plan
# ---------------------------------------------------------------------------
@router.post("/plan/generate", summary="Generate a new meal plan")
async def generate_plan(user: User = Depends(get_current_user)):
    """
    Generate and persist a fresh weekly meal plan for the authenticated user.

    The plan is based on the user's profile (target calories, dietary preference,
    allergies). Automatically filters halal / vegetarian / vegan as configured.
    Falls back to a healthy template plan if the recipe database is empty.

    Returns HTTP 400 if the user has not completed their profile yet.
    """
    try:
        plan = await generate_meal_plan(user.id)
    except Exception as exc:
        logger.exception(f"Error generating meal plan for user {user.id}: {exc}")
        raise HTTPException(status_code=500, detail="Failed to generate meal plan")

    if plan is None:
        raise HTTPException(
            status_code=400,
            detail="Profile not found. Please complete the health questionnaire first.",
        )

    return {
        "plan": plan,
        "message": "Meal plan generated successfully.",
    }


# ---------------------------------------------------------------------------
# GET /{recipe_id} — recipe details with ingredients
# ---------------------------------------------------------------------------
@router.get("/{recipe_id}", summary="Get recipe details")
async def get_recipe(
    recipe_id: int,
    user: User = Depends(get_current_user),
):
    """
    Return full details for a single recipe including its ingredient list.

    Returns HTTP 404 if the recipe_id does not exist in the database.
    """
    async with async_session() as session:
        result = await session.execute(
            select(Recipe).where(Recipe.id == recipe_id)
        )
        recipe = result.scalar_one_or_none()

        if not recipe:
            raise HTTPException(status_code=404, detail=f"Recipe {recipe_id} not found")

        result = await session.execute(
            select(RecipeIngredient)
            .where(RecipeIngredient.recipe_id == recipe_id)
            .order_by(RecipeIngredient.id)
        )
        ingredients = result.scalars().all()

    return {
        "id": recipe.id,
        "title_en": recipe.title_en,
        "title_ru": recipe.title_ru,
        "image_url": recipe.image_url,
        "source_url": recipe.source_url,
        "instructions": recipe.instructions,
        "instructions_ru": recipe.instructions_ru,
        "instructions_json": recipe.instructions_json,
        "youtube_url": recipe.youtube_url,
        "cook_time_mins": recipe.cook_time_mins,
        "servings": recipe.servings,
        "calories_per_serving": recipe.calories_per_serving,
        "protein": recipe.protein,
        "carbs": recipe.carbs,
        "fat": recipe.fat,
        "diet_type": recipe.diet_type,
        "cuisine": recipe.cuisine,
        "source_api": recipe.source_api,
        "ingredients": [
            {
                "name": i.name,
                "amount": i.amount,
                "unit": i.unit,
            }
            for i in ingredients
        ],
    }
