"""TheMealDB collector — free, unlimited recipe data with no API key required."""
import logging
import re

import aiohttp
from sqlalchemy import select

from app.database import async_session, Recipe

logger = logging.getLogger(__name__)

BASE_URL = "https://www.themealdb.com/api/json/v1/1"

# Categories to iterate over in fetch_all_categories()
DEFAULT_CATEGORIES: list[str] = [
    "Chicken",
    "Beef",
    "Seafood",
    "Vegetarian",
    "Lamb",
    "Pasta",
    "Side",
]

# Maximum meals fetched per category (TheMealDB has ~20-30 per category)
_MAX_PER_CATEGORY = 20


async def fetch_meals_by_category(category: str = "Chicken") -> int:
    """
    Fetch meals from TheMealDB for a given category and persist them to the Recipe table.

    Workflow:
      1. GET /filter.php?c=<category>  →  list of {idMeal, strMeal, strMealThumb}
      2. For each meal (up to _MAX_PER_CATEGORY), GET /lookup.php?i=<idMeal> → full details
      3. Skip meals whose title already exists in the DB for source_api="themealdb"
      4. Persist title, image, instructions, cuisine, source_url to Recipe row

    Args:
        category: TheMealDB category name (case-sensitive as per their API).

    Returns:
        Number of new recipes inserted.
    """
    logger.info(f"TheMealDB: fetching category '{category}'")
    inserted = 0

    try:
        async with aiohttp.ClientSession() as client:
            # Step 1: list of meals in the category
            async with client.get(
                f"{BASE_URL}/filter.php",
                params={"c": category},
                timeout=aiohttp.ClientTimeout(total=20),
            ) as resp:
                if resp.status != 200:
                    logger.warning(f"TheMealDB filter: HTTP {resp.status} for category '{category}'")
                    return 0
                list_data = await resp.json()

            meals = list_data.get("meals") or []
            if not meals:
                logger.info(f"TheMealDB: no meals found for category '{category}'")
                return 0

            logger.info(f"TheMealDB: {len(meals)} meals listed for '{category}' — fetching up to {_MAX_PER_CATEGORY}")
            meals = meals[:_MAX_PER_CATEGORY]

            async with async_session() as session:
                for meal_stub in meals:
                    meal_id = meal_stub.get("idMeal")
                    meal_title = (meal_stub.get("strMeal") or "").strip()
                    if not meal_id or not meal_title:
                        continue

                    # Idempotency: skip if title + source already in DB
                    existing = await session.execute(
                        select(Recipe).where(
                            Recipe.source_api == "themealdb",
                            Recipe.title_en == meal_title,
                        )
                    )
                    if existing.scalar_one_or_none():
                        continue

                    # Step 2: full details for this meal
                    try:
                        async with client.get(
                            f"{BASE_URL}/lookup.php",
                            params={"i": meal_id},
                            timeout=aiohttp.ClientTimeout(total=15),
                        ) as detail_resp:
                            if detail_resp.status != 200:
                                logger.debug(f"TheMealDB lookup failed for meal {meal_id}: HTTP {detail_resp.status}")
                                continue
                            detail_data = await detail_resp.json()
                    except aiohttp.ClientError as exc:
                        logger.warning(f"TheMealDB: network error fetching meal {meal_id}: {exc}")
                        continue

                    details_list = detail_data.get("meals") or []
                    if not details_list:
                        continue
                    details = details_list[0]

                    # Build ingredient list string for instructions context
                    ingredients_text = _extract_ingredients_text(details)

                    instructions_raw = (details.get("strInstructions") or "").strip()
                    if ingredients_text:
                        full_instructions = f"Ingredients:\n{ingredients_text}\n\nInstructions:\n{instructions_raw}"
                    else:
                        full_instructions = instructions_raw or None

                    # Parse instructions into step array
                    raw_steps = [s.strip() for s in instructions_raw.replace("\r\n", "\n").split("\n") if s.strip()]
                    # Remove numbered prefixes like "1." "STEP 1" etc.
                    clean_steps = []
                    for s in raw_steps:
                        cleaned = re.sub(r'^(STEP\s+)?\d+[\.\)]\s*', '', s, flags=re.IGNORECASE).strip()
                        if cleaned and len(cleaned) > 5:  # Skip very short fragments
                            clean_steps.append(cleaned)

                    recipe = Recipe(
                        title_en=meal_title,
                        source_url=details.get("strSource") or details.get("strYoutube"),
                        image_url=details.get("strMealThumb"),
                        instructions=full_instructions,
                        instructions_json=clean_steps if clean_steps else None,
                        youtube_url=details.get("strYoutube") or None,
                        cuisine=details.get("strArea"),
                        source_api="themealdb",
                        # TheMealDB does not provide macro data — left null
                        calories_per_serving=None,
                        protein=None,
                        carbs=None,
                        fat=None,
                        cook_time_mins=None,
                        servings=None,
                        diet_type=_infer_diet_type(category),
                    )
                    session.add(recipe)
                    inserted += 1

                await session.commit()

        logger.info(f"TheMealDB '{category}': {inserted} new recipes saved")
        return inserted

    except aiohttp.ClientError as exc:
        logger.error(f"TheMealDB network error for category '{category}': {exc}")
        return 0
    except Exception as exc:
        logger.exception(f"Unexpected error in fetch_meals_by_category('{category}'): {exc}")
        return 0


async def fetch_all_categories(
    categories: list[str] | None = None,
) -> int:
    """
    Fetch meals from multiple TheMealDB categories sequentially.

    Args:
        categories: List of category names to fetch. Defaults to DEFAULT_CATEGORIES.

    Returns:
        Total number of new recipes inserted across all categories.
    """
    cats = categories or DEFAULT_CATEGORIES
    total = 0
    for cat in cats:
        count = await fetch_meals_by_category(cat)
        total += count
    logger.info(f"TheMealDB fetch_all_categories: {total} total new recipes across {len(cats)} categories")
    return total


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------
def _extract_ingredients_text(details: dict) -> str:
    """
    TheMealDB encodes up to 20 ingredient/measure pairs as parallel numbered keys:
      strIngredient1 / strMeasure1  …  strIngredient20 / strMeasure20

    Returns a formatted multi-line string listing all non-empty pairs.
    """
    lines: list[str] = []
    for i in range(1, 21):
        ingredient = (details.get(f"strIngredient{i}") or "").strip()
        measure = (details.get(f"strMeasure{i}") or "").strip()
        if ingredient:
            if measure:
                lines.append(f"- {measure} {ingredient}")
            else:
                lines.append(f"- {ingredient}")
    return "\n".join(lines)


def _infer_diet_type(category: str) -> str | None:
    """
    Infer a diet_type label from the TheMealDB category name.

    TheMealDB's Vegetarian category contains plant-based meals.
    All others are treated as halal (pork-free categories are assumed).
    """
    cat_lower = category.lower()
    if cat_lower == "vegetarian":
        return "vegetarian"
    # TheMealDB does not offer pork-only categories; all others are assumed halal-friendly
    return "halal"
