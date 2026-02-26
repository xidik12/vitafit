"""Scheduler jobs — data seeding, daily tasks, cleanup."""
import json
import logging
from pathlib import Path
from sqlalchemy import select

from app.database import async_session, FoodItem, Recipe, RecipeIngredient

logger = logging.getLogger(__name__)


async def seed_global_foods():
    """Load comprehensive global food database into the database (incremental)."""
    foods_path = Path(__file__).parent.parent / "data" / "common_foods_global.json"
    if not foods_path.exists():
        logger.warning("common_foods_global.json not found — skipping seed")
        return

    with open(foods_path, encoding="utf-8") as f:
        foods = json.load(f)

    # Query all existing name_en values for source="custom_global" in one shot
    async with async_session() as session:
        result = await session.execute(
            select(FoodItem.name_en).where(FoodItem.source == "custom_global")
        )
        existing_names: set[str] = {row[0] for row in result.all()}

    # Insert only foods whose name_en is not already in the DB
    async with async_session() as session:
        added = 0
        for item in foods:
            name_en = item.get("name_en", "")
            if name_en in existing_names:
                continue
            fi = FoodItem(
                name_en=name_en,
                name_ru=item.get("name_ru", ""),
                source="custom_global",
                calories_per_100g=item.get("calories_per_100g"),
                protein_per_100g=item.get("protein_per_100g"),
                carbs_per_100g=item.get("carbs_per_100g"),
                fat_per_100g=item.get("fat_per_100g"),
                serving_size_g=item.get("serving_size_g", 100),
                image_url=item.get("image_url"),
            )
            session.add(fi)
            added += 1
        await session.commit()
        skipped = len(existing_names)
        logger.info(
            f"Global foods: {added} new items added, {skipped} already existed "
            f"(total in JSON: {len(foods)})"
        )


async def seed_recipes():
    """Load seed recipes with images, instructions, and ingredients into the database."""
    recipes_path = Path(__file__).parent.parent / "data" / "seed_recipes.json"
    if not recipes_path.exists():
        logger.warning("seed_recipes.json not found — skipping recipe seed")
        return

    async with async_session() as session:
        # Idempotent check — skip if already seeded
        result = await session.execute(
            select(Recipe).where(Recipe.source_api == "seed").limit(1)
        )
        if result.scalar_one_or_none():
            logger.info("Recipes already seeded")
            return

    with open(recipes_path, encoding="utf-8") as f:
        recipes = json.load(f)

    async with async_session() as session:
        count = 0
        for item in recipes:
            recipe = Recipe(
                title_en=item.get("title_en", ""),
                title_ru=item.get("title_ru"),
                image_url=item.get("image_url"),
                instructions=item.get("instructions"),
                instructions_ru=item.get("instructions_ru"),
                instructions_json=item.get("instructions_json"),
                cook_time_mins=item.get("cook_time_mins"),
                servings=item.get("servings"),
                calories_per_serving=item.get("calories_per_serving"),
                protein=item.get("protein"),
                carbs=item.get("carbs"),
                fat=item.get("fat"),
                diet_type=item.get("diet_type", "halal"),
                cuisine=item.get("cuisine", "international"),
                source_api="seed",
                youtube_url=item.get("youtube_url"),
            )
            session.add(recipe)
            await session.flush()  # Get recipe.id for ingredients

            for ing in item.get("ingredients", []):
                amount_raw = ing.get("amount")
                try:
                    amount_val = float(amount_raw) if amount_raw is not None else None
                except (ValueError, TypeError):
                    amount_val = None
                ri = RecipeIngredient(
                    recipe_id=recipe.id,
                    name=ing.get("name", ""),
                    amount=amount_val,
                    unit=ing.get("unit"),
                )
                session.add(ri)
            count += 1

        await session.commit()
        logger.info(f"Seeded {count} recipes with ingredients")
