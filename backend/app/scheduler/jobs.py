"""Scheduler jobs — data seeding, daily tasks, cleanup."""
import json
import logging
from pathlib import Path
from sqlalchemy import select

from app.database import async_session, FoodItem

logger = logging.getLogger(__name__)


async def seed_russian_foods():
    """Load common Russian foods into the database."""
    foods_path = Path(__file__).parent.parent / "data" / "common_foods_ru.json"
    if not foods_path.exists():
        logger.warning("common_foods_ru.json not found — skipping seed")
        return

    async with async_session() as session:
        # Check if already seeded
        result = await session.execute(
            select(FoodItem).where(FoodItem.source == "custom_ru").limit(1)
        )
        if result.scalar_one_or_none():
            logger.info("Russian foods already seeded")
            return

    with open(foods_path, encoding="utf-8") as f:
        foods = json.load(f)

    async with async_session() as session:
        count = 0
        for item in foods:
            fi = FoodItem(
                name_en=item.get("name_en", ""),
                name_ru=item.get("name_ru", ""),
                source="custom_ru",
                calories_per_100g=item.get("calories_per_100g"),
                protein_per_100g=item.get("protein_per_100g"),
                carbs_per_100g=item.get("carbs_per_100g"),
                fat_per_100g=item.get("fat_per_100g"),
                serving_size_g=item.get("serving_size_g", 100),
            )
            session.add(fi)
            count += 1
        await session.commit()
        logger.info(f"Seeded {count} Russian food items")
