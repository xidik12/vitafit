"""Data sync jobs — exercise DB loading, recipe fetching."""
import logging

logger = logging.getLogger(__name__)


async def sync_exercise_db():
    """Load exercises from Free Exercise DB if not already loaded."""
    try:
        from app.collectors.exercise_db import load_exercises
        await load_exercises()
    except Exception as e:
        logger.error(f"Exercise DB sync failed: {e}")


async def sync_recipes():
    """Fetch recipes from external APIs."""
    try:
        from app.collectors.spoonacular import fetch_recipes
        await fetch_recipes(diet="halal", number=20)
    except Exception as e:
        logger.error(f"Spoonacular sync failed: {e}")

    try:
        from app.collectors.themealdb import fetch_all_categories
        await fetch_all_categories()
    except Exception as e:
        logger.error(f"TheMealDB sync failed: {e}")
