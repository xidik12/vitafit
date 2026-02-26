"""Meal plan generation — personalized weekly meal plans with halal filtering."""
import logging
import random

from sqlalchemy import select

from app.database import (
    async_session, UserProfile, Recipe, MealPlan, ExercisePlan, RecipeIngredient,
)

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


def is_halal(recipe: Recipe, ingredient_names: list[str] | None = None) -> bool:
    """
    Return True if the recipe contains no haram ingredients.
    Checks the English title *and* ingredient names against HARAM_INGREDIENTS.
    """
    title = (recipe.title_en or "").lower()
    for word in HARAM_INGREDIENTS:
        if word in title:
            return False

    # Ingredient-level check
    if ingredient_names:
        for ing_name in ingredient_names:
            ing_lower = ing_name.lower()
            for word in HARAM_INGREDIENTS:
                if word in ing_lower:
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

        # Pre-load all recipe ingredients for allergen/halal ingredient-level checks
        recipe_ids = [r.id for r in all_recipes]
        ingredient_map: dict[int, list[str]] = {}
        if recipe_ids:
            ing_result = await session.execute(
                select(RecipeIngredient).where(
                    RecipeIngredient.recipe_id.in_(recipe_ids)
                )
            )
            for ing in ing_result.scalars().all():
                ingredient_map.setdefault(ing.recipe_id, []).append(ing.name)

        # Fetch the latest ExercisePlan for training-day awareness
        ep_result = await session.execute(
            select(ExercisePlan)
            .where(ExercisePlan.user_id == user_id)
            .order_by(ExercisePlan.week_number.desc())
            .limit(1)
        )
        exercise_plan = ep_result.scalar_one_or_none()

    # ------------------------------------------------------------------
    # Profile fields with safe defaults
    # ------------------------------------------------------------------
    target_cals = profile.target_calories or 2000
    dietary_pref = (profile.dietary_pref or "halal").lower().strip()
    allergies_raw = profile.allergies or ""
    allergy_words = [a.strip().lower() for a in allergies_raw.split(",") if a.strip()]

    # Macro targets from profile (grams per day)
    target_protein = profile.target_protein or 0
    target_carbs = profile.target_carbs or 0
    target_fat = profile.target_fat or 0

    # ------------------------------------------------------------------
    # Filter recipes by dietary preference (with ingredient-level checks)
    # ------------------------------------------------------------------
    filtered: list[Recipe] = list(all_recipes)

    if dietary_pref in ("halal", "none", ""):
        filtered = [
            r for r in filtered
            if is_halal(r, ingredient_map.get(r.id))
        ]
    elif dietary_pref == "vegetarian":
        filtered = [r for r in filtered if r.diet_type in ("vegetarian", "vegan")]
    elif dietary_pref == "vegan":
        filtered = [r for r in filtered if r.diet_type == "vegan"]

    # Filter out allergens from the title AND ingredient names
    if allergy_words:
        def _no_allergens(r: Recipe) -> bool:
            title = (r.title_en or "").lower()
            if any(a in title for a in allergy_words):
                return False
            # Ingredient-level allergen check
            for ing_name in ingredient_map.get(r.id, []):
                if any(a in ing_name.lower() for a in allergy_words):
                    return False
            return True
        filtered = [r for r in filtered if _no_allergens(r)]

    # ------------------------------------------------------------------
    # No recipes in DB -> return template plan
    # ------------------------------------------------------------------
    if not filtered:
        logger.info(f"User {user_id}: no matching recipes in DB — using template plan")
        plan = _generate_template_plan(target_cals, dietary_pref)
    else:
        plan = _build_plan_from_db(
            user_id, filtered, target_cals,
            target_protein=target_protein,
            target_carbs=target_carbs,
            target_fat=target_fat,
            exercise_plan=exercise_plan,
        )

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
# Exercise plan helpers — determine workout vs rest days
# ---------------------------------------------------------------------------
def _get_workout_days(exercise_plan: ExercisePlan | None) -> set[int]:
    """
    Return a set of day numbers (1-7) that are workout days.
    Reads from the exercise plan's plan_json["days"] list.
    Days with type == "rest" or no exercises are rest days.
    If no exercise plan exists, assume all days are rest days.
    """
    if not exercise_plan or not exercise_plan.plan_json:
        return set()

    plan_data = exercise_plan.plan_json
    days = plan_data.get("days", [])
    workout_days: set[int] = set()
    for day_info in days:
        day_num = day_info.get("day", 0)
        day_type = day_info.get("type", "")
        exercises = day_info.get("exercises", [])
        if day_type != "rest" and exercises:
            workout_days.add(day_num)
    return workout_days


# ---------------------------------------------------------------------------
# DB-backed plan builder
# ---------------------------------------------------------------------------
def _build_plan_from_db(
    user_id: int,
    recipes: list[Recipe],
    target_cals: int,
    *,
    target_protein: int = 0,
    target_carbs: int = 0,
    target_fat: int = 0,
    exercise_plan: ExercisePlan | None = None,
) -> dict:
    """Build a 7-day plan using real recipe rows from the database."""

    # ------------------------------------------------------------------
    # Filter out recipes without images (with fallback)
    # ------------------------------------------------------------------
    recipes_with_images = [
        r for r in recipes
        if r.image_url and r.image_url.strip()
    ]
    if len(recipes_with_images) >= 10:
        recipes = recipes_with_images
    else:
        logger.info(
            f"User {user_id}: only {len(recipes_with_images)} recipes have images "
            f"(< 10 threshold) — keeping all {len(recipes)} recipes"
        )

    # ------------------------------------------------------------------
    # Determine workout vs rest days
    # ------------------------------------------------------------------
    workout_days = _get_workout_days(exercise_plan)

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

    # Track used recipe IDs across the entire week for variety
    used_ids: set[int] = set()

    for day_num in range(1, 8):
        is_workout_day = day_num in workout_days

        # Adjust macros for training vs rest day
        if target_carbs > 0:
            if is_workout_day:
                day_carbs = int(target_carbs * 1.10)  # +10% carbs
                day_protein = target_protein
            else:
                day_carbs = int(target_carbs * 0.90)  # -10% carbs
                day_protein = int(target_protein * 1.05) if target_protein > 0 else 0  # +5% protein
        else:
            day_carbs = target_carbs
            day_protein = target_protein
        day_fat = target_fat

        # Per-meal calorie split
        breakfast_cals = int(target_cals * 0.25)
        lunch_cals = int(target_cals * 0.35)
        dinner_cals = int(target_cals * 0.30)
        snack_cals = int(target_cals * 0.10)

        # Per-meal macro split (same percentages as calories)
        def _split_macro(daily_val: int, pct: float) -> float:
            return daily_val * pct if daily_val > 0 else 0.0

        breakfast = _pick_meal(
            recipes, breakfast_cals,
            target_protein=_split_macro(day_protein, 0.25),
            target_carbs=_split_macro(day_carbs, 0.25),
            target_fat=_split_macro(day_fat, 0.25),
            exclude_ids=used_ids,
        )
        if breakfast and breakfast.get("recipe_id"):
            used_ids.add(breakfast["recipe_id"])

        lunch = _pick_meal(
            recipes, lunch_cals,
            target_protein=_split_macro(day_protein, 0.35),
            target_carbs=_split_macro(day_carbs, 0.35),
            target_fat=_split_macro(day_fat, 0.35),
            exclude_ids=used_ids,
        )
        if lunch and lunch.get("recipe_id"):
            used_ids.add(lunch["recipe_id"])

        dinner = _pick_meal(
            recipes, dinner_cals,
            target_protein=_split_macro(day_protein, 0.30),
            target_carbs=_split_macro(day_carbs, 0.30),
            target_fat=_split_macro(day_fat, 0.30),
            exclude_ids=used_ids,
        )
        if dinner and dinner.get("recipe_id"):
            used_ids.add(dinner["recipe_id"])

        snacks = _pick_meal(
            recipes, snack_cals,
            target_protein=_split_macro(day_protein, 0.10),
            target_carbs=_split_macro(day_carbs, 0.10),
            target_fat=_split_macro(day_fat, 0.10),
            exclude_ids=used_ids,
        )
        if snacks and snacks.get("recipe_id"):
            used_ids.add(snacks["recipe_id"])

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
        day_entry: dict = {
            "day": day_num,
            "meals": meals,
            "total_calories": round(total_cals),
        }
        if workout_days:
            day_entry["is_workout_day"] = is_workout_day

        plan["days"].append(day_entry)

    return plan


def _pick_meal(
    recipes: list[Recipe],
    target_cals: int,
    *,
    target_protein: float = 0.0,
    target_carbs: float = 0.0,
    target_fat: float = 0.0,
    exclude_ids: set[int] | None = None,
) -> dict | None:
    """
    Pick a recipe whose calories and macros are closest to the targets.

    Scoring: abs(cal_diff) + abs(protein_diff)*2 + abs(carb_diff) + abs(fat_diff)
    Protein is weighted 2x because hitting protein targets is more important.

    Among the 5 closest candidates, choose one randomly for variety.
    Recipes in ``exclude_ids`` are skipped for variety enforcement.
    If no recipes have calorie data, pick any random recipe (not in exclude set).
    """
    if not recipes:
        return None

    _exclude = exclude_ids or set()

    # Filter out already-used recipes for variety
    available = [r for r in recipes if r.id not in _exclude]
    if not available:
        # Fallback: if all recipes exhausted, allow repeats
        available = list(recipes)

    with_cals = [r for r in available if r.calories_per_serving is not None]
    if not with_cals:
        r = random.choice(available)
        return _recipe_to_dict(r)

    use_macros = target_protein > 0 or target_carbs > 0 or target_fat > 0

    def _score(r: Recipe) -> float:
        cal_diff = abs((r.calories_per_serving or 0) - target_cals)
        if not use_macros:
            return cal_diff
        protein_diff = abs((r.protein or 0) - target_protein)
        carbs_diff = abs((r.carbs or 0) - target_carbs)
        fat_diff = abs((r.fat or 0) - target_fat)
        return cal_diff + protein_diff * 2 + carbs_diff + fat_diff

    sorted_recipes = sorted(with_cals, key=_score)
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
        "instructions": r.instructions,
        "instructions_ru": r.instructions_ru,
        "instructions_json": r.instructions_json,
        "youtube_url": r.youtube_url,
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
            "image_url": "https://images.unsplash.com/photo-1517673400267-0251440c45dc?w=400&h=300&fit=crop",
            "instructions_json": ["Bring water or milk to a boil.", "Add oats and reduce heat, cook 5 minutes.", "Slice banana and drizzle honey on top.", "Serve warm."],
        },
        {
            "title_en": "Scrambled eggs with wholegrain toast",
            "title_ru": "Яичница-болтунья с цельнозерновым тостом",
            "calories": 420, "protein": 22, "carbs": 38, "fat": 18,
            "cook_time_mins": 10, "vegan": False,
            "image_url": "https://images.unsplash.com/photo-1525351484163-7529414344d8?w=400&h=300&fit=crop",
            "instructions_json": ["Crack eggs into a bowl, whisk with salt and pepper.", "Melt butter in a pan over medium heat.", "Pour eggs in and stir gently until just set.", "Toast bread and serve alongside."],
        },
        {
            "title_en": "Greek yogurt with granola and berries",
            "title_ru": "Греческий йогурт с гранолой и ягодами",
            "calories": 310, "protein": 16, "carbs": 42, "fat": 9,
            "cook_time_mins": 5, "vegan": False,
            "image_url": "https://images.unsplash.com/photo-1488477181946-6428a0291777?w=400&h=300&fit=crop",
            "instructions_json": ["Spoon Greek yogurt into a bowl.", "Top with granola and mixed berries.", "Drizzle with honey if desired.", "Serve immediately."],
        },
        {
            "title_en": "Smoothie bowl with chia seeds",
            "title_ru": "Смузи боул с семенами чиа",
            "calories": 370, "protein": 10, "carbs": 62, "fat": 11,
            "cook_time_mins": 8, "vegan": True,
            "image_url": "https://images.unsplash.com/photo-1502741224143-90386d7f8c82?w=400&h=300&fit=crop",
            "instructions_json": ["Blend frozen berries, banana, and almond milk until thick.", "Pour into a bowl.", "Top with chia seeds, sliced fruit, and granola.", "Serve cold."],
        },
        {
            "title_en": "Avocado toast with poached eggs",
            "title_ru": "Тост с авокадо и яйцом пашот",
            "calories": 440, "protein": 18, "carbs": 40, "fat": 22,
            "cook_time_mins": 12, "vegan": False,
            "image_url": "https://images.unsplash.com/photo-1541519227354-08fa5d50c44d?w=400&h=300&fit=crop",
            "instructions_json": ["Toast bread until golden.", "Mash avocado with lemon juice, salt and pepper.", "Spread avocado on toast.", "Poach eggs in simmering water for 3 minutes and place on top."],
        },
        {
            "title_en": "Overnight oats with almond milk",
            "title_ru": "Ночная овсянка на миндальном молоке",
            "calories": 330, "protein": 11, "carbs": 55, "fat": 8,
            "cook_time_mins": 5, "vegan": True,
            "image_url": "https://images.unsplash.com/photo-1490474418585-ba9bad8fd0ea?w=400&h=300&fit=crop",
            "instructions_json": ["Mix oats, almond milk, and chia seeds in a jar.", "Refrigerate overnight (at least 6 hours).", "In the morning, stir and top with fresh fruit.", "Serve cold."],
        },
    ]

    lunch_options = [
        {
            "title_en": "Grilled chicken breast with brown rice and steamed broccoli",
            "title_ru": "Куриная грудка на гриле с бурым рисом и брокколи",
            "calories": 550, "protein": 42, "carbs": 58, "fat": 10,
            "cook_time_mins": 25, "vegan": False,
            "image_url": "https://images.unsplash.com/photo-1532550907401-a500c9a57435?w=400&h=300&fit=crop",
            "instructions_json": ["Season chicken breast with salt, pepper, and olive oil.", "Grill on medium-high heat 6-7 minutes per side.", "Cook brown rice according to package directions.", "Steam broccoli for 4 minutes and serve together."],
        },
        {
            "title_en": "Baked salmon with quinoa salad",
            "title_ru": "Запечённый лосось с салатом из киноа",
            "calories": 520, "protein": 38, "carbs": 42, "fat": 20,
            "cook_time_mins": 30, "vegan": False,
            "image_url": "https://images.unsplash.com/photo-1467003909585-2f8a72700288?w=400&h=300&fit=crop",
            "instructions_json": ["Preheat oven to 200C/400F.", "Season salmon with lemon, dill, salt and pepper.", "Bake for 15-18 minutes.", "Cook quinoa and toss with cucumber, tomato, and olive oil.", "Serve salmon over quinoa salad."],
        },
        {
            "title_en": "Red lentil soup with wholegrain bread",
            "title_ru": "Суп из красной чечевицы с цельнозерновым хлебом",
            "calories": 460, "protein": 22, "carbs": 68, "fat": 9,
            "cook_time_mins": 30, "vegan": True,
            "image_url": "https://images.unsplash.com/photo-1547592166-23ac45744acd?w=400&h=300&fit=crop",
            "instructions_json": ["Saute onion, garlic, and carrots in olive oil.", "Add red lentils, vegetable broth, and cumin.", "Simmer for 20-25 minutes until lentils are soft.", "Blend partially for creamy texture.", "Serve with wholegrain bread."],
        },
        {
            "title_en": "Turkey and vegetable wrap",
            "title_ru": "Ролл с индейкой и овощами",
            "calories": 490, "protein": 32, "carbs": 52, "fat": 14,
            "cook_time_mins": 15, "vegan": False,
            "image_url": "https://images.unsplash.com/photo-1626700051175-6818013e1d4f?w=400&h=300&fit=crop",
            "instructions_json": ["Warm a large tortilla.", "Layer sliced turkey, lettuce, tomato, and avocado.", "Add a drizzle of yogurt sauce.", "Roll tightly and slice in half."],
        },
        {
            "title_en": "Chickpea and spinach curry with basmati rice",
            "title_ru": "Карри из нута со шпинатом и рисом басмати",
            "calories": 480, "protein": 18, "carbs": 72, "fat": 12,
            "cook_time_mins": 25, "vegan": True,
            "image_url": "https://images.unsplash.com/photo-1565557623262-b51c2513a641?w=400&h=300&fit=crop",
            "instructions_json": ["Saute onion, ginger, and garlic in oil.", "Add curry powder, cumin, and turmeric.", "Stir in chickpeas and coconut milk, simmer 15 mins.", "Fold in spinach until wilted.", "Serve over basmati rice."],
        },
        {
            "title_en": "Tuna salad with mixed greens and olive oil dressing",
            "title_ru": "Салат с тунцом, зеленью и оливковым маслом",
            "calories": 430, "protein": 35, "carbs": 20, "fat": 24,
            "cook_time_mins": 10, "vegan": False,
            "image_url": "https://images.unsplash.com/photo-1512621776951-a57141f2eefd?w=400&h=300&fit=crop",
            "instructions_json": ["Drain tuna and flake into a bowl.", "Toss mixed greens with cherry tomatoes and cucumber.", "Add tuna on top.", "Drizzle with olive oil and lemon juice."],
        },
    ]

    dinner_options = [
        {
            "title_en": "Baked salmon with steamed broccoli and sweet potato",
            "title_ru": "Запечённый лосось с брокколи и бататом",
            "calories": 470, "protein": 36, "carbs": 40, "fat": 16,
            "cook_time_mins": 30, "vegan": False,
            "image_url": "https://images.unsplash.com/photo-1467003909585-2f8a72700288?w=400&h=300&fit=crop",
            "instructions_json": ["Preheat oven to 200C/400F.", "Place salmon on a lined baking tray, season well.", "Cube sweet potato and roast for 25 minutes.", "Steam broccoli and serve everything together."],
        },
        {
            "title_en": "Beef and vegetable stir-fry with jasmine rice",
            "title_ru": "Говядина с овощами и рисом жасмин",
            "calories": 530, "protein": 32, "carbs": 52, "fat": 18,
            "cook_time_mins": 20, "vegan": False,
            "image_url": "https://images.unsplash.com/photo-1546833999-b9f581a1996d?w=400&h=300&fit=crop",
            "instructions_json": ["Slice beef thinly and marinate in soy sauce and ginger.", "Cook jasmine rice.", "Stir-fry beef in a hot wok for 2 minutes, set aside.", "Stir-fry bell peppers, broccoli, and carrots.", "Return beef, toss together and serve over rice."],
        },
        {
            "title_en": "Chicken tikka masala with brown rice",
            "title_ru": "Куриная тикка масала с бурым рисом",
            "calories": 540, "protein": 36, "carbs": 56, "fat": 14,
            "cook_time_mins": 35, "vegan": False,
            "image_url": "https://images.unsplash.com/photo-1565557623262-b51c2513a641?w=400&h=300&fit=crop",
            "instructions_json": ["Marinate chicken in yogurt and spices for 30 minutes.", "Grill or pan-fry chicken pieces until charred.", "Simmer tomato sauce with cream and spices.", "Add chicken to sauce and cook 10 more minutes.", "Serve over brown rice."],
        },
        {
            "title_en": "Baked cod with roasted sweet potato and greens",
            "title_ru": "Запечённая треска с печёным бататом и зеленью",
            "calories": 400, "protein": 32, "carbs": 44, "fat": 8,
            "cook_time_mins": 30, "vegan": False,
            "image_url": "https://images.unsplash.com/photo-1559737558-2f5a35f4523b?w=400&h=300&fit=crop",
            "instructions_json": ["Preheat oven to 190C/375F.", "Season cod with lemon, garlic, and herbs.", "Roast sweet potato wedges for 20 minutes.", "Bake cod for 12-15 minutes.", "Serve with steamed greens."],
        },
        {
            "title_en": "Vegetable tofu stir-fry with soba noodles",
            "title_ru": "Тофу с овощами и лапшой соба",
            "calories": 420, "protein": 20, "carbs": 60, "fat": 12,
            "cook_time_mins": 20, "vegan": True,
            "image_url": "https://images.unsplash.com/photo-1546069901-ba9599a7e63c?w=400&h=300&fit=crop",
            "instructions_json": ["Press tofu and cut into cubes.", "Cook soba noodles according to package.", "Stir-fry tofu until golden, add vegetables.", "Toss noodles with soy-sesame sauce and serve."],
        },
        {
            "title_en": "Black bean and vegetable burrito bowl",
            "title_ru": "Боул буррито с чёрными бобами и овощами",
            "calories": 490, "protein": 20, "carbs": 70, "fat": 14,
            "cook_time_mins": 20, "vegan": True,
            "image_url": "https://images.unsplash.com/photo-1512058564366-18510be2db19?w=400&h=300&fit=crop",
            "instructions_json": ["Cook rice and season with lime juice.", "Heat black beans with cumin and garlic.", "Saute peppers and onions.", "Assemble bowl with rice, beans, veggies, salsa, and avocado."],
        },
    ]

    snack_options = [
        {
            "title_en": "Mixed nuts and dried fruit",
            "title_ru": "Ореховый микс с сухофруктами",
            "calories": 200, "protein": 5, "carbs": 18, "fat": 14,
            "cook_time_mins": 0, "vegan": True,
            "image_url": "https://images.unsplash.com/photo-1599599810769-bcde5a160d32?w=400&h=300&fit=crop",
            "instructions_json": ["Combine almonds, walnuts, and cashews.", "Add dried cranberries and apricots.", "Mix well and portion into servings."],
        },
        {
            "title_en": "Apple slices with almond butter",
            "title_ru": "Дольки яблока с миндальной пастой",
            "calories": 210, "protein": 5, "carbs": 28, "fat": 10,
            "cook_time_mins": 2, "vegan": True,
            "image_url": "https://images.unsplash.com/photo-1488459716781-31db52582fe9?w=400&h=300&fit=crop",
            "instructions_json": ["Wash and slice apple into wedges.", "Spread almond butter on each slice.", "Sprinkle with cinnamon if desired."],
        },
        {
            "title_en": "Cottage cheese with fresh berries",
            "title_ru": "Творог со свежими ягодами",
            "calories": 155, "protein": 16, "carbs": 14, "fat": 4,
            "cook_time_mins": 2, "vegan": False,
            "image_url": "https://images.unsplash.com/photo-1488477181946-6428a0291777?w=400&h=300&fit=crop",
            "instructions_json": ["Spoon cottage cheese into a bowl.", "Top with fresh strawberries and blueberries.", "Serve immediately."],
        },
        {
            "title_en": "Rice cakes with avocado",
            "title_ru": "Рисовые хлебцы с авокадо",
            "calories": 180, "protein": 3, "carbs": 24, "fat": 9,
            "cook_time_mins": 3, "vegan": True,
            "image_url": "https://images.unsplash.com/photo-1541519227354-08fa5d50c44d?w=400&h=300&fit=crop",
            "instructions_json": ["Mash avocado with a fork.", "Spread on rice cakes.", "Season with salt, pepper, and chili flakes."],
        },
        {
            "title_en": "Greek yogurt with honey",
            "title_ru": "Греческий йогурт с мёдом",
            "calories": 160, "protein": 12, "carbs": 20, "fat": 4,
            "cook_time_mins": 1, "vegan": False,
            "image_url": "https://images.unsplash.com/photo-1488477181946-6428a0291777?w=400&h=300&fit=crop",
            "instructions_json": ["Spoon Greek yogurt into a bowl.", "Drizzle with honey.", "Top with a few walnuts if desired."],
        },
        {
            "title_en": "Hummus with carrot and cucumber sticks",
            "title_ru": "Хумус с морковью и огурцом",
            "calories": 175, "protein": 6, "carbs": 22, "fat": 8,
            "cook_time_mins": 5, "vegan": True,
            "image_url": "https://images.unsplash.com/photo-1540420773420-3366772f4999?w=400&h=300&fit=crop",
            "instructions_json": ["Cut carrots and cucumbers into sticks.", "Spoon hummus into a small dish.", "Arrange veggies around the hummus and serve."],
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
