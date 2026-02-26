"""Meal plan generation — personalized weekly meal plans with halal filtering."""
import logging
import random

from sqlalchemy import select

from app.database import async_session, UserProfile, Recipe, MealPlan

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Haram ingredient set — checked against recipe title (lowercase)
# ---------------------------------------------------------------------------
HARAM_INGREDIENTS: frozenset[str] = frozenset({
    "pork",
    "bacon",
    "ham",
    "prosciutto",
    "salami",
    "pepperoni",
    "chorizo",
    "lard",
    "gelatin",
    "pork chop",
    "pork loin",
    "pork belly",
    "pork ribs",
    "spare rib",
    "sausage",
    "hotdog",
    "hot dog",
    "wine",
    "beer",
    "rum",
    "vodka",
    "whiskey",
    "whisky",
    "brandy",
    "champagne",
    "liqueur",
    "liquor",
    "marsala",
    "mirin",
    "sake",
    "sherry",
    "bourbon",
    "tequila",
    "gin",
})


def is_halal(recipe: Recipe) -> bool:
    """
    Return True if the recipe contains no haram ingredients.
    Checks the English title against HARAM_INGREDIENTS.
    """
    title = (recipe.title_en or "").lower()
    for word in HARAM_INGREDIENTS:
        if word in title:
            return False
    return True


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------
async def generate_meal_plan(user_id: int) -> dict | None:
    """
    Generate a personalized 7-day meal plan for the given user.

    Reads UserProfile for target_calories and dietary_pref.
    Filters available Recipe rows accordingly (halal / vegetarian / vegan).
    Falls back to a hardcoded template plan if the DB has no matching recipes.
    Persists the plan to MealPlan with an incrementing week_number.

    Returns the plan dict on success, or None if the user has no profile.
    """
    async with async_session() as session:
        result = await session.execute(
            select(UserProfile).where(UserProfile.user_id == user_id)
        )
        profile = result.scalar_one_or_none()
        if not profile:
            logger.warning(f"generate_meal_plan: no profile for user {user_id}")
            return None

        result = await session.execute(select(Recipe))
        all_recipes = result.scalars().all()

    # ------------------------------------------------------------------
    # Profile fields with safe defaults
    # ------------------------------------------------------------------
    target_cals = profile.target_calories or 2000
    dietary_pref = (profile.dietary_pref or "halal").lower().strip()
    allergies_raw = profile.allergies or ""
    allergy_words = [a.strip().lower() for a in allergies_raw.split(",") if a.strip()]

    # ------------------------------------------------------------------
    # Filter recipes by dietary preference
    # ------------------------------------------------------------------
    filtered: list[Recipe] = list(all_recipes)

    if dietary_pref in ("halal", "none", ""):
        filtered = [r for r in filtered if is_halal(r)]
    elif dietary_pref == "vegetarian":
        filtered = [r for r in filtered if r.diet_type in ("vegetarian", "vegan")]
    elif dietary_pref == "vegan":
        filtered = [r for r in filtered if r.diet_type == "vegan"]

    # Filter out allergens from the title as a best-effort guard
    if allergy_words:
        def _no_allergens(r: Recipe) -> bool:
            title = (r.title_en or "").lower()
            return not any(a in title for a in allergy_words)
        filtered = [r for r in filtered if _no_allergens(r)]

    # ------------------------------------------------------------------
    # No recipes in DB → return template plan
    # ------------------------------------------------------------------
    if not filtered:
        logger.info(f"User {user_id}: no matching recipes in DB — using template plan")
        plan = _generate_template_plan(target_cals, dietary_pref)
    else:
        plan = _build_plan_from_db(user_id, filtered, target_cals)

    # ------------------------------------------------------------------
    # Persist to DB
    # ------------------------------------------------------------------
    async with async_session() as session:
        result = await session.execute(
            select(MealPlan)
            .where(MealPlan.user_id == user_id)
            .order_by(MealPlan.week_number.desc())
            .limit(1)
        )
        last = result.scalar_one_or_none()
        week = (last.week_number + 1) if last else 1

        mp = MealPlan(user_id=user_id, week_number=week, plan_json=plan)
        session.add(mp)
        await session.commit()
        logger.info(f"Saved MealPlan week {week} for user {user_id}")

    return plan


# ---------------------------------------------------------------------------
# DB-backed plan builder
# ---------------------------------------------------------------------------
def _build_plan_from_db(
    user_id: int,
    recipes: list[Recipe],
    target_cals: int,
) -> dict:
    """Build a 7-day plan using real recipe rows from the database."""
    breakfast_cals = int(target_cals * 0.25)
    lunch_cals = int(target_cals * 0.35)
    dinner_cals = int(target_cals * 0.30)
    snack_cals = int(target_cals * 0.10)

    plan = {
        "user_id": user_id,
        "total_days": 7,
        "target_calories": target_cals,
        "calorie_split": {
            "breakfast_pct": 25,
            "lunch_pct": 35,
            "dinner_pct": 30,
            "snacks_pct": 10,
        },
        "template": False,
        "days": [],
    }

    for day_num in range(1, 8):
        breakfast = _pick_meal(recipes, breakfast_cals)
        lunch = _pick_meal(recipes, lunch_cals)
        dinner = _pick_meal(recipes, dinner_cals)
        snacks = _pick_meal(recipes, snack_cals)

        meals = {
            "breakfast": breakfast,
            "lunch": lunch,
            "dinner": dinner,
            "snacks": snacks,
        }
        total_cals = sum(
            m.get("calories") or 0
            for m in meals.values()
            if m is not None
        )
        plan["days"].append({
            "day": day_num,
            "meals": meals,
            "total_calories": round(total_cals),
        })

    return plan


def _pick_meal(recipes: list[Recipe], target_cals: int) -> dict | None:
    """
    Pick a recipe whose calorie count is closest to target_cals.
    Among the 5 closest candidates, choose one randomly for variety.
    If no recipes have calorie data, pick any random recipe.
    """
    if not recipes:
        return None

    with_cals = [r for r in recipes if r.calories_per_serving is not None]
    if not with_cals:
        r = random.choice(recipes)
        return _recipe_to_dict(r)

    sorted_recipes = sorted(
        with_cals, key=lambda r: abs((r.calories_per_serving or 0) - target_cals)
    )
    pool = sorted_recipes[:5]
    return _recipe_to_dict(random.choice(pool))


def _recipe_to_dict(r: Recipe) -> dict:
    return {
        "recipe_id": r.id,
        "title_en": r.title_en,
        "title_ru": r.title_ru,
        "image_url": r.image_url,
        "calories": r.calories_per_serving,
        "protein": r.protein,
        "carbs": r.carbs,
        "fat": r.fat,
        "cook_time_mins": r.cook_time_mins,
        "source_url": r.source_url,
    }


# ---------------------------------------------------------------------------
# Hardcoded template plan (fallback when DB is empty)
# ---------------------------------------------------------------------------
def _generate_template_plan(target_cals: int, dietary_pref: str) -> dict:
    """
    Generate a healthy template meal plan when no recipes are in the DB.
    Includes bilingual (EN/RU) meal names and macro approximations.
    Automatically excludes meat-based meals for vegetarian/vegan preferences.
    """
    breakfast_cals = int(target_cals * 0.25)
    lunch_cals = int(target_cals * 0.35)
    dinner_cals = int(target_cals * 0.30)
    snack_cals = int(target_cals * 0.10)

    # ---- Template meal pools ----

    breakfast_options = [
        {
            "title_en": "Oatmeal with banana and honey",
            "title_ru": "Овсянка с бананом и мёдом",
            "calories": 350, "protein": 12, "carbs": 58, "fat": 7,
            "cook_time_mins": 10, "vegan": True,
        },
        {
            "title_en": "Scrambled eggs with wholegrain toast",
            "title_ru": "Яичница-болтунья с цельнозерновым тостом",
            "calories": 420, "protein": 22, "carbs": 38, "fat": 18,
            "cook_time_mins": 10, "vegan": False,
        },
        {
            "title_en": "Greek yogurt with granola and berries",
            "title_ru": "Греческий йогурт с гранолой и ягодами",
            "calories": 310, "protein": 16, "carbs": 42, "fat": 9,
            "cook_time_mins": 5, "vegan": False,
        },
        {
            "title_en": "Smoothie bowl with chia seeds",
            "title_ru": "Смузи боул с семенами чиа",
            "calories": 370, "protein": 10, "carbs": 62, "fat": 11,
            "cook_time_mins": 8, "vegan": True,
        },
        {
            "title_en": "Avocado toast with poached eggs",
            "title_ru": "Тост с авокадо и яйцом пашот",
            "calories": 440, "protein": 18, "carbs": 40, "fat": 22,
            "cook_time_mins": 12, "vegan": False,
        },
        {
            "title_en": "Overnight oats with almond milk",
            "title_ru": "Ночная овсянка на миндальном молоке",
            "calories": 330, "protein": 11, "carbs": 55, "fat": 8,
            "cook_time_mins": 5, "vegan": True,
        },
    ]

    lunch_options = [
        {
            "title_en": "Grilled chicken breast with brown rice and steamed broccoli",
            "title_ru": "Куриная грудка на гриле с бурым рисом и брокколи",
            "calories": 550, "protein": 42, "carbs": 58, "fat": 10,
            "cook_time_mins": 25, "vegan": False,
        },
        {
            "title_en": "Baked salmon with quinoa salad",
            "title_ru": "Запечённый лосось с салатом из киноа",
            "calories": 520, "protein": 38, "carbs": 42, "fat": 20,
            "cook_time_mins": 30, "vegan": False,
        },
        {
            "title_en": "Red lentil soup with wholegrain bread",
            "title_ru": "Суп из красной чечевицы с цельнозерновым хлебом",
            "calories": 460, "protein": 22, "carbs": 68, "fat": 9,
            "cook_time_mins": 30, "vegan": True,
        },
        {
            "title_en": "Turkey and vegetable wrap",
            "title_ru": "Ролл с индейкой и овощами",
            "calories": 490, "protein": 32, "carbs": 52, "fat": 14,
            "cook_time_mins": 15, "vegan": False,
        },
        {
            "title_en": "Chickpea and spinach curry with basmati rice",
            "title_ru": "Карри из нута со шпинатом и рисом басмати",
            "calories": 480, "protein": 18, "carbs": 72, "fat": 12,
            "cook_time_mins": 25, "vegan": True,
        },
        {
            "title_en": "Tuna salad with mixed greens and olive oil dressing",
            "title_ru": "Салат с тунцом, зеленью и оливковым маслом",
            "calories": 430, "protein": 35, "carbs": 20, "fat": 24,
            "cook_time_mins": 10, "vegan": False,
        },
    ]

    dinner_options = [
        {
            "title_en": "Baked salmon with steamed broccoli and sweet potato",
            "title_ru": "Запечённый лосось с брокколи и бататом",
            "calories": 470, "protein": 36, "carbs": 40, "fat": 16,
            "cook_time_mins": 30, "vegan": False,
        },
        {
            "title_en": "Beef and vegetable stir-fry with jasmine rice",
            "title_ru": "Говядина с овощами и рисом жасмин",
            "calories": 530, "protein": 32, "carbs": 52, "fat": 18,
            "cook_time_mins": 20, "vegan": False,
        },
        {
            "title_en": "Chicken tikka masala with brown rice",
            "title_ru": "Куриная тикка масала с бурым рисом",
            "calories": 540, "protein": 36, "carbs": 56, "fat": 14,
            "cook_time_mins": 35, "vegan": False,
        },
        {
            "title_en": "Baked cod with roasted sweet potato and greens",
            "title_ru": "Запечённая треска с печёным бататом и зеленью",
            "calories": 400, "protein": 32, "carbs": 44, "fat": 8,
            "cook_time_mins": 30, "vegan": False,
        },
        {
            "title_en": "Vegetable tofu stir-fry with soba noodles",
            "title_ru": "Тофу с овощами и лапшой соба",
            "calories": 420, "protein": 20, "carbs": 60, "fat": 12,
            "cook_time_mins": 20, "vegan": True,
        },
        {
            "title_en": "Black bean and vegetable burrito bowl",
            "title_ru": "Боул буррито с чёрными бобами и овощами",
            "calories": 490, "protein": 20, "carbs": 70, "fat": 14,
            "cook_time_mins": 20, "vegan": True,
        },
    ]

    snack_options = [
        {
            "title_en": "Mixed nuts and dried fruit",
            "title_ru": "Ореховый микс с сухофруктами",
            "calories": 200, "protein": 5, "carbs": 18, "fat": 14,
            "cook_time_mins": 0, "vegan": True,
        },
        {
            "title_en": "Apple slices with almond butter",
            "title_ru": "Дольки яблока с миндальной пастой",
            "calories": 210, "protein": 5, "carbs": 28, "fat": 10,
            "cook_time_mins": 2, "vegan": True,
        },
        {
            "title_en": "Cottage cheese with fresh berries",
            "title_ru": "Творог со свежими ягодами",
            "calories": 155, "protein": 16, "carbs": 14, "fat": 4,
            "cook_time_mins": 2, "vegan": False,
        },
        {
            "title_en": "Rice cakes with avocado",
            "title_ru": "Рисовые хлебцы с авокадо",
            "calories": 180, "protein": 3, "carbs": 24, "fat": 9,
            "cook_time_mins": 3, "vegan": True,
        },
        {
            "title_en": "Greek yogurt with honey",
            "title_ru": "Греческий йогурт с мёдом",
            "calories": 160, "protein": 12, "carbs": 20, "fat": 4,
            "cook_time_mins": 1, "vegan": False,
        },
        {
            "title_en": "Hummus with carrot and cucumber sticks",
            "title_ru": "Хумус с морковью и огурцом",
            "calories": 175, "protein": 6, "carbs": 22, "fat": 8,
            "cook_time_mins": 5, "vegan": True,
        },
    ]

    # Apply dietary filters to the template pools
    def _filter_pool(pool: list[dict]) -> list[dict]:
        if dietary_pref == "vegan":
            return [m for m in pool if m.get("vegan", False)]
        elif dietary_pref == "vegetarian":
            # Vegetarians eat dairy/eggs but not meat — approximate by "vegan" flag
            # (template doesn't mark vegetarian separately; vegan is a safe subset)
            veg = [m for m in pool if m.get("vegan", False)]
            return veg if veg else pool
        return pool  # halal / none — all template meals are halal

    bf_pool = _filter_pool(breakfast_options) or breakfast_options
    lu_pool = _filter_pool(lunch_options) or lunch_options
    di_pool = _filter_pool(dinner_options) or dinner_options
    sn_pool = _filter_pool(snack_options) or snack_options

    plan = {
        "total_days": 7,
        "target_calories": target_cals,
        "calorie_split": {
            "breakfast_pct": 25,
            "lunch_pct": 35,
            "dinner_pct": 30,
            "snacks_pct": 10,
        },
        "template": True,
        "dietary_pref": dietary_pref,
        "days": [],
    }

    for day_num in range(1, 8):
        breakfast = random.choice(bf_pool).copy()
        lunch = random.choice(lu_pool).copy()
        dinner = random.choice(di_pool).copy()
        snacks = random.choice(sn_pool).copy()

        # Remove internal "vegan" flag from output
        for meal in (breakfast, lunch, dinner, snacks):
            meal.pop("vegan", None)

        total_cals = (
            (breakfast.get("calories") or 0)
            + (lunch.get("calories") or 0)
            + (dinner.get("calories") or 0)
            + (snacks.get("calories") or 0)
        )

        plan["days"].append({
            "day": day_num,
            "meals": {
                "breakfast": breakfast,
                "lunch": lunch,
                "dinner": dinner,
                "snacks": snacks,
            },
            "total_calories": total_cals,
        })

    return plan
