"""Exercise DB collector — loads exercises from the Free Exercise DB (public domain JSON)."""
import logging

import aiohttp
from sqlalchemy import select, func

from app.database import async_session, Exercise

logger = logging.getLogger(__name__)

EXERCISE_DB_URL = (
    "https://raw.githubusercontent.com/yuhonas/free-exercise-db/main/dist/exercises.json"
)

# Mapping from Free Exercise DB level → our difficulty enum
_LEVEL_MAP: dict[str, str] = {
    "beginner": "beginner",
    "intermediate": "intermediate",
    "expert": "advanced",
}

# Mapping from Free Exercise DB category → our exercise_type enum
_CATEGORY_MAP: dict[str, str] = {
    "strength": "strength",
    "stretching": "flexibility",
    "plyometrics": "cardio",
    "cardio": "cardio",
    "powerlifting": "strength",
    "olympic weightlifting": "strength",
    "strongman": "strength",
    "yoga": "flexibility",
}


async def load_exercises() -> int:
    """
    Fetch and persist exercises from the Free Exercise DB (yuhonas/free-exercise-db).

    Skips loading if exercises already exist in the DB (idempotent).
    Maps fields:
      name        → Exercise.name_en
      primaryMuscles[0] → body_part + target_muscle
      equipment   → equipment
      level       → difficulty (beginner/intermediate/advanced)
      category    → exercise_type (strength/cardio/flexibility)
      instructions (list) → joined by newline into instructions text
      images      → stored as JSON array in images column

    Returns:
        Number of exercises inserted (0 if already loaded or on error).
    """
    # Idempotency check
    async with async_session() as session:
        count_result = await session.execute(
            select(func.count()).select_from(Exercise)
        )
        existing_count = count_result.scalar_one()

    if existing_count > 0:
        logger.info(f"Exercises already loaded ({existing_count} records) — skipping fetch")
        return 0

    logger.info(f"Fetching exercises from Free Exercise DB: {EXERCISE_DB_URL}")
    try:
        async with aiohttp.ClientSession() as client:
            async with client.get(
                EXERCISE_DB_URL,
                timeout=aiohttp.ClientTimeout(total=60),
            ) as resp:
                if resp.status != 200:
                    logger.error(f"Free Exercise DB: HTTP {resp.status}")
                    return 0
                data = await resp.json(content_type=None)

        if not isinstance(data, list):
            logger.error("Free Exercise DB: unexpected response format (not a list)")
            return 0

        logger.info(f"Downloaded {len(data)} exercises — inserting into DB...")

        inserted = 0
        async with async_session() as session:
            for item in data:
                name = (item.get("name") or "").strip()
                if not name:
                    continue  # Skip nameless entries

                primary_muscles = item.get("primaryMuscles") or []
                body_part = primary_muscles[0] if primary_muscles else None
                target_muscle = primary_muscles[0] if primary_muscles else None

                secondary = item.get("secondaryMuscles") or []
                # If primary is empty but secondary exists, use first secondary
                if not body_part and secondary:
                    body_part = secondary[0]

                raw_level = (item.get("level") or "beginner").lower().strip()
                difficulty = _LEVEL_MAP.get(raw_level, "intermediate")

                raw_category = (item.get("category") or "strength").lower().strip()
                exercise_type = _CATEGORY_MAP.get(raw_category, "strength")

                instructions_list = item.get("instructions") or []
                instructions_text = "\n".join(
                    str(step).strip() for step in instructions_list if step
                )

                images = item.get("images")
                if isinstance(images, list) and images:
                    # Prefix with the GitHub raw base path used by the project
                    images = [
                        f"https://raw.githubusercontent.com/yuhonas/free-exercise-db/main/exercises/{img}"
                        if not str(img).startswith("http") else str(img)
                        for img in images
                    ]

                ex = Exercise(
                    name_en=name,
                    body_part=body_part,
                    target_muscle=target_muscle,
                    equipment=item.get("equipment") or "body only",
                    difficulty=difficulty,
                    instructions=instructions_text or None,
                    images=images,
                    source="free_exercise_db",
                    exercise_type=exercise_type,
                )
                session.add(ex)
                inserted += 1

            await session.commit()

        logger.info(f"Free Exercise DB: {inserted} exercises saved to DB")
        return inserted

    except aiohttp.ClientError as exc:
        logger.error(f"Network error fetching Free Exercise DB: {exc}")
        return 0
    except Exception as exc:
        logger.exception(f"Unexpected error in load_exercises: {exc}")
        return 0
