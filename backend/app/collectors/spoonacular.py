"""Spoonacular API collector — recipes with full nutrition data."""
import logging

import aiohttp
from sqlalchemy import select

from app.config import settings
from app.database import async_session, Recipe, RecipeIngredient

logger = logging.getLogger(__name__)

BASE_URL = "https://api.spoonacular.com"

# Halal exclude list for the excludeIngredients API parameter
_HALAL_EXCLUDE = "pork,bacon,ham,lard,gelatin,wine,beer,rum,prosciutto,salami,pepperoni,chorizo"


# ---------------------------------------------------------------------------
# Public helpers
# ---------------------------------------------------------------------------
async def fetch_recipes(diet: str = "halal", number: int = 20) -> int:
    """
    Fetch recipes from the Spoonacular /recipes/complexSearch endpoint and
    persist them to the Recipe + RecipeIngredient tables.

    Halal mode: excludes pork, alcohol derivatives via excludeIngredients.
    Vegetarian / vegan: uses Spoonacular's native diet filter.
    Skips any recipe whose spoonacular_id already exists in the DB.

    Args:
        diet: "halal" | "vegetarian" | "vegan" | "none"
        number: Number of recipes to request (Spoonacular max is 100 per call).

    Returns:
        Number of new recipes inserted.
    """
    if not settings.spoonacular_api_key:
        logger.warning("SPOONACULAR_API_KEY not set — skipping Spoonacular fetch")
        return 0

    params: dict = {
        "apiKey": settings.spoonacular_api_key,
        "number": number,
        "addRecipeNutrition": True,
        "instructionsRequired": True,
        "fillIngredients": True,
        "addRecipeInformation": True,
    }

    if diet == "vegetarian":
        params["diet"] = "vegetarian"
    elif diet == "vegan":
        params["diet"] = "vegan"

    # Always apply halal exclusions unless diet is already a subset (veg/vegan)
    if diet in ("halal", "none"):
        params["excludeIngredients"] = _HALAL_EXCLUDE

    try:
        async with aiohttp.ClientSession() as client:
            async with client.get(
                f"{BASE_URL}/recipes/complexSearch",
                params=params,
                timeout=aiohttp.ClientTimeout(total=30),
            ) as resp:
                if resp.status != 200:
                    body = await resp.text()
                    logger.error(
                        f"Spoonacular API error: HTTP {resp.status} — {body[:200]}"
                    )
                    return 0
                data = await resp.json()

        recipes = data.get("results") or []
        logger.info(f"Spoonacular returned {len(recipes)} recipes for diet='{diet}'")

        inserted = 0
        async with async_session() as session:
            for item in recipes:
                spoonacular_id = item.get("id")
                if spoonacular_id is None:
                    continue

                # Idempotency — skip if already in DB
                existing = await session.execute(
                    select(Recipe).where(Recipe.spoonacular_id == spoonacular_id)
                )
                if existing.scalar_one_or_none():
                    continue

                # Parse nutrition
                nutrition = item.get("nutrition") or {}
                nutrients_list = nutrition.get("nutrients") or []
                nutrients = {n["name"]: n.get("amount") for n in nutrients_list}

                recipe = Recipe(
                    title_en=item.get("title") or "",
                    source_url=item.get("sourceUrl"),
                    image_url=item.get("image"),
                    instructions=item.get("instructions") or None,
                    cook_time_mins=item.get("readyInMinutes"),
                    servings=item.get("servings"),
                    calories_per_serving=nutrients.get("Calories"),
                    protein=nutrients.get("Protein"),
                    carbs=nutrients.get("Carbohydrates"),
                    fat=nutrients.get("Fat"),
                    diet_type=diet,
                    cuisine=_first_cuisine(item.get("cuisines")),
                    source_api="spoonacular",
                    spoonacular_id=spoonacular_id,
                )
                session.add(recipe)
                await session.flush()  # Get recipe.id for FK in ingredients

                # Persist extended ingredients
                for ing in item.get("extendedIngredients") or []:
                    ri = RecipeIngredient(
                        recipe_id=recipe.id,
                        name=ing.get("name") or ing.get("nameClean") or "",
                        amount=ing.get("amount"),
                        unit=ing.get("unit") or ing.get("measures", {}).get("metric", {}).get("unitShort"),
                    )
                    session.add(ri)

                inserted += 1

            await session.commit()

        logger.info(f"Spoonacular: {inserted} new recipes saved to DB (diet={diet})")
        return inserted

    except aiohttp.ClientError as exc:
        logger.error(f"Spoonacular network error: {exc}")
        return 0
    except Exception as exc:
        logger.exception(f"Unexpected error in fetch_recipes: {exc}")
        return 0


async def search_recipes(
    query: str,
    diet: str = "halal",
    number: int = 10,
) -> list[dict]:
    """
    Search Spoonacular for recipes matching the given text query.

    Does not persist results to DB — returns raw result list for on-the-fly use.

    Args:
        query: Free-text search term (e.g. "chicken soup").
        diet: "halal" | "vegetarian" | "vegan" | "none"
        number: Max number of results to return.

    Returns:
        List of recipe dicts as returned by Spoonacular, or empty list on error.
    """
    if not settings.spoonacular_api_key:
        logger.warning("SPOONACULAR_API_KEY not set — search_recipes returning empty")
        return []

    params: dict = {
        "apiKey": settings.spoonacular_api_key,
        "query": query,
        "number": number,
        "addRecipeNutrition": True,
        "instructionsRequired": True,
    }

    if diet == "halal":
        params["excludeIngredients"] = _HALAL_EXCLUDE
    elif diet in ("vegetarian", "vegan"):
        params["diet"] = diet

    try:
        async with aiohttp.ClientSession() as client:
            async with client.get(
                f"{BASE_URL}/recipes/complexSearch",
                params=params,
                timeout=aiohttp.ClientTimeout(total=15),
            ) as resp:
                if resp.status != 200:
                    logger.error(f"Spoonacular search: HTTP {resp.status}")
                    return []
                data = await resp.json()

        results = data.get("results") or []
        logger.info(f"Spoonacular search '{query}': {len(results)} results")
        return results

    except aiohttp.ClientError as exc:
        logger.error(f"Spoonacular search network error: {exc}")
        return []
    except Exception as exc:
        logger.exception(f"Unexpected error in search_recipes: {exc}")
        return []


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------
def _first_cuisine(cuisines: list | None) -> str | None:
    """Return the first cuisine string if the list is non-empty, else None."""
    if cuisines and isinstance(cuisines, list):
        return cuisines[0]
    return None
