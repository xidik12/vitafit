"""Exercise plan generation — personalized weekly workout plans."""
import json
import logging
import random
from pathlib import Path

from sqlalchemy import select

from app.database import async_session, UserProfile, Exercise, ExercisePlan

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Load tai chi moves at module level
# ---------------------------------------------------------------------------
_tai_chi_path = Path(__file__).parent.parent / "data" / "tai_chi_moves.json"
TAI_CHI_MOVES: list[dict] = []
if _tai_chi_path.exists():
    with open(_tai_chi_path, encoding="utf-8") as _f:
        TAI_CHI_MOVES = json.load(_f)
    logger.info(f"Loaded {len(TAI_CHI_MOVES)} tai chi moves")
else:
    logger.warning(f"tai_chi_moves.json not found at {_tai_chi_path}")


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------
async def generate_exercise_plan(user_id: int) -> dict | None:
    """
    Generate a personalized 7-day exercise plan for the given user.

    Returns the plan dict on success, or None if the user has no profile.
    Also persists the plan to the ExercisePlan table with an incrementing
    week_number.
    """
    async with async_session() as session:
        result = await session.execute(
            select(UserProfile).where(UserProfile.user_id == user_id)
        )
        profile = result.scalar_one_or_none()
        if not profile:
            logger.warning(f"generate_exercise_plan: no profile for user {user_id}")
            return None

        # Fetch all exercises from DB for use in plan generation
        result = await session.execute(select(Exercise))
        exercises = result.scalars().all()

    # ------------------------------------------------------------------
    # Read profile fields with safe defaults
    # ------------------------------------------------------------------
    age = profile.age or 30
    goal = (profile.goal or "health").lower().strip()
    parq_passed = profile.parq_passed if profile.parq_passed is not None else True
    activity = (profile.activity_level or "moderate").lower().strip()
    equipment_raw = profile.equipment or ""
    equipment = [e.strip().lower() for e in equipment_raw.split(",") if e.strip()]
    time_per_week = profile.time_per_week_mins or 150

    # Age group determines intensity caps and exercise selection
    if age >= 65:
        age_group = "senior"
    elif age >= 40:
        age_group = "middle"
    else:
        age_group = "young"

    # Number of workout days per week based on activity level
    days_map = {
        "sedentary": 3,
        "light": 3,
        "moderate": 4,
        "active": 5,
        "very_active": 6,
    }
    workout_days = days_map.get(activity, 4)
    # Cap seniors at 4 workout days regardless of stated activity
    if age_group == "senior":
        workout_days = min(workout_days, 4)

    time_per_session = max(20, time_per_week // workout_days)

    # ------------------------------------------------------------------
    # PAR-Q failed → gentle plan only (walking + stretching + tai chi beginner)
    # ------------------------------------------------------------------
    if not parq_passed:
        logger.info(f"User {user_id}: PAR-Q failed — generating gentle plan")
        plan = _generate_gentle_plan(
            user_id=user_id,
            age_group=age_group,
            workout_days=workout_days,
            time_per_session=time_per_session,
            exercises=exercises,
        )
    else:
        # ------------------------------------------------------------------
        # Goal-based plan
        # ------------------------------------------------------------------
        plan = _generate_goal_plan(
            user_id=user_id,
            goal=goal,
            age_group=age_group,
            workout_days=workout_days,
            time_per_session=time_per_session,
            exercises=exercises,
            equipment=equipment,
        )

    # ------------------------------------------------------------------
    # Persist to DB
    # ------------------------------------------------------------------
    async with async_session() as session:
        result = await session.execute(
            select(ExercisePlan)
            .where(ExercisePlan.user_id == user_id)
            .order_by(ExercisePlan.week_number.desc())
            .limit(1)
        )
        last_plan = result.scalar_one_or_none()
        week = (last_plan.week_number + 1) if last_plan else 1

        ep = ExercisePlan(user_id=user_id, week_number=week, plan_json=plan)
        session.add(ep)
        await session.commit()
        logger.info(f"Saved ExercisePlan week {week} for user {user_id}")

    return plan


# ---------------------------------------------------------------------------
# Gentle plan (PAR-Q failed)
# ---------------------------------------------------------------------------
def _generate_gentle_plan(
    user_id: int,
    age_group: str,
    workout_days: int,
    time_per_session: int,
    exercises: list,
) -> dict:
    """
    Safe plan for users who failed PAR-Q screening.
    Contains only: gentle walking, beginner tai chi, full-body stretching.
    """
    plan = {
        "user_id": user_id,
        "goal": "gentle_health",
        "age_group": age_group,
        "total_days": 7,
        "workout_days": workout_days,
        "gentle": True,
        "parq_note": "Plan adjusted for medical screening — consult your doctor before increasing intensity.",
        "days": [],
    }

    beginner_tai_chi = [m for m in TAI_CHI_MOVES if m["difficulty"] == "beginner"]

    for day_num in range(1, 8):
        if day_num > workout_days:
            plan["days"].append({"day": day_num, "type": "rest", "exercises": [], "duration_mins": 0})
            continue

        day_exercises: list[dict] = []

        # 1. Gentle walking warm-up
        walk_mins = min(15, time_per_session // 3)
        day_exercises.append({
            "name_en": "Gentle Walking",
            "name_ru": "Лёгкая ходьба",
            "type": "cardio",
            "duration_mins": walk_mins,
            "intensity": "low",
            "instructions_en": "Walk at a comfortable, easy pace. Focus on steady breathing.",
            "instructions_ru": "Идите в комфортном темпе. Сосредоточьтесь на ровном дыхании.",
        })

        # 2. Beginner tai chi moves (4 randomly chosen)
        if beginner_tai_chi:
            selected_moves = random.sample(beginner_tai_chi, min(4, len(beginner_tai_chi)))
            for move in selected_moves:
                day_exercises.append({
                    "name_en": move["name_en"],
                    "name_ru": move["name_ru"],
                    "type": "tai_chi",
                    "duration_mins": move["duration_mins"],
                    "instructions": move["instructions"],
                    "difficulty": move["difficulty"],
                })

        # 3. Full-body cool-down stretch
        day_exercises.append({
            "name_en": "Full Body Gentle Stretch",
            "name_ru": "Мягкая растяжка всего тела",
            "type": "flexibility",
            "duration_mins": 10,
            "intensity": "low",
            "instructions_en": "Hold each stretch for 20-30 seconds. Never force or bounce. Breathe deeply.",
            "instructions_ru": "Удерживайте каждое растяжение 20-30 секунд. Не форсируйте движения. Дышите глубоко.",
        })

        plan["days"].append({
            "day": day_num,
            "type": "workout",
            "exercises": day_exercises,
            "duration_mins": time_per_session,
        })

    return plan


# ---------------------------------------------------------------------------
# Goal-based plan dispatcher
# ---------------------------------------------------------------------------
def _generate_goal_plan(
    user_id: int,
    goal: str,
    age_group: str,
    workout_days: int,
    time_per_session: int,
    exercises: list,
    equipment: list[str],
) -> dict:
    """Route to goal-specific plan builder."""
    plan = {
        "user_id": user_id,
        "goal": goal,
        "age_group": age_group,
        "total_days": 7,
        "workout_days": workout_days,
        "gentle": False,
        "days": [],
    }

    for day_num in range(1, 8):
        if day_num > workout_days:
            plan["days"].append({
                "day": day_num,
                "type": "rest",
                "exercises": [],
                "duration_mins": 0,
                "note": "Rest and recovery day.",
            })
            continue

        if goal == "weight_loss":
            day_exercises = _weight_loss_day(day_num, age_group, exercises, time_per_session, equipment)
        elif goal == "muscle":
            day_exercises = _muscle_day(day_num, age_group, exercises, time_per_session, equipment)
        elif goal == "flexibility":
            day_exercises = _flexibility_day(day_num, age_group, time_per_session)
        elif goal == "stress_relief":
            day_exercises = _stress_relief_day(day_num, age_group, time_per_session)
        else:
            # "health" and any unknown goal → balanced plan
            day_exercises = _general_health_day(day_num, age_group, exercises, time_per_session, equipment)

        plan["days"].append({
            "day": day_num,
            "type": "workout",
            "exercises": day_exercises,
            "duration_mins": time_per_session,
        })

    return plan


# ---------------------------------------------------------------------------
# Goal-specific day builders
# ---------------------------------------------------------------------------
def _weight_loss_day(
    day_num: int,
    age_group: str,
    exercises: list,
    time_per_session: int,
    equipment: list[str],
) -> list[dict]:
    """
    Weight loss: cardio warm-up + compound strength circuit + cool-down stretch.
    Alternates muscle group targets each day to ensure full-body coverage.
    """
    day_exercises: list[dict] = []

    # --- Cardio warm-up ---
    cardio_mins = max(10, time_per_session // 3)
    cardio_pool = _bodyweight_fallback("cardio", 2)
    for c in cardio_pool:
        c = c.copy()
        c["duration_mins"] = cardio_mins // len(cardio_pool)
        day_exercises.append(c)

    # --- Strength circuit (rotate body part each day) ---
    body_parts = ["chest", "legs", "back", "core", "arms", "shoulders", "full_body"]
    target = body_parts[(day_num - 1) % len(body_parts)]
    sets = 3 if age_group == "young" else 2
    reps = 15 if age_group == "young" else 12

    db_ex = _pick_exercises(exercises, body_part=target, ex_type="strength", count=3)
    day_exercises.extend(_resolve_exercises(db_ex, sets=sets, reps=reps))

    # --- Cool-down stretch ---
    stretches = _bodyweight_fallback("flexibility", 2)
    day_exercises.extend(stretches)

    return day_exercises


def _muscle_day(
    day_num: int,
    age_group: str,
    exercises: list,
    time_per_session: int,
    equipment: list[str],
) -> list[dict]:
    """
    Muscle building: progressive overload split.
    Young: 4x8 heavy | Middle: 3x10 moderate | Senior: 3x12 light
    Rotating push/pull/legs split across the week.
    """
    # Push/Pull/Legs/Shoulders/Arms/Legs2 split
    splits = {
        1: "chest",
        2: "back",
        3: "legs",
        4: "shoulders",
        5: "arms",
        6: "legs",
        7: "core",
    }
    target = splits.get(day_num, "full_body")

    if age_group == "young":
        sets, reps = 4, 8
    elif age_group == "middle":
        sets, reps = 3, 10
    else:
        sets, reps = 3, 12

    db_ex = _pick_exercises(exercises, body_part=target, ex_type="strength", count=4)
    day_exercises = _resolve_exercises(db_ex, sets=sets, reps=reps)

    # Supplement with bodyweight if DB returned fewer than 4
    if len(day_exercises) < 4:
        fallback = _bodyweight_fallback("strength", 4 - len(day_exercises))
        for ex in fallback:
            ex = ex.copy()
            ex["sets"] = sets
            ex["reps"] = reps
        day_exercises.extend(fallback)

    return day_exercises


def _flexibility_day(
    day_num: int,
    age_group: str,
    time_per_session: int,
) -> list[dict]:
    """
    Flexibility: alternates between full tai chi sessions and yoga/stretching days.
    Seniors always get beginner-only tai chi; young/middle get intermediate too.
    """
    day_exercises: list[dict] = []

    if day_num % 2 == 1:
        # Tai chi day — select moves appropriate to age group
        allowed_difficulties = (
            ["beginner"] if age_group == "senior"
            else ["beginner", "intermediate"]
        )
        pool = [m for m in TAI_CHI_MOVES if m["difficulty"] in allowed_difficulties]
        count = min(6, len(pool))
        selected = random.sample(pool, count) if pool else []
        for move in selected:
            day_exercises.append({
                "name_en": move["name_en"],
                "name_ru": move["name_ru"],
                "type": "tai_chi",
                "duration_mins": move["duration_mins"],
                "instructions": move["instructions"],
                "difficulty": move["difficulty"],
            })
    else:
        # Yoga / deep stretching day
        stretches = _bodyweight_fallback("flexibility", 4)
        day_exercises.extend(stretches)
        day_exercises.append({
            "name_en": "Diaphragmatic Deep Breathing",
            "name_ru": "Диафрагмальное глубокое дыхание",
            "type": "flexibility",
            "duration_mins": 5,
            "instructions_en": "Lie on your back. Place one hand on the chest, one on the belly. Breathe deeply so only the belly hand rises. 5 seconds in, hold 2, 5 seconds out.",
            "instructions_ru": "Лягте на спину. Одну руку положите на грудь, другую на живот. Дышите глубоко так, чтобы поднималась только рука на животе. 5 секунд вдох, задержка 2, 5 секунд выдох.",
        })

    return day_exercises


def _stress_relief_day(
    day_num: int,
    age_group: str,
    time_per_session: int,
) -> list[dict]:
    """
    Stress relief: mindful walking + tai chi (beginner) + progressive muscle relaxation.
    Always calm, low-intensity, meditative in nature.
    """
    day_exercises: list[dict] = []

    # Mindful walk
    day_exercises.append({
        "name_en": "Mindful Walking",
        "name_ru": "Осознанная ходьба",
        "type": "cardio",
        "duration_mins": 15,
        "intensity": "low",
        "instructions_en": "Walk slowly. Notice each footstep. Breathe in for 4 steps, out for 4 steps. Let thoughts pass without engaging.",
        "instructions_ru": "Идите медленно. Замечайте каждый шаг. Вдыхайте на 4 шага, выдыхайте на 4 шага. Позвольте мыслям проходить мимо.",
    })

    # Beginner tai chi (5 moves)
    beginner_moves = [m for m in TAI_CHI_MOVES if m["difficulty"] == "beginner"]
    if beginner_moves:
        selected = random.sample(beginner_moves, min(5, len(beginner_moves)))
        for move in selected:
            day_exercises.append({
                "name_en": move["name_en"],
                "name_ru": move["name_ru"],
                "type": "tai_chi",
                "duration_mins": move["duration_mins"],
                "instructions": move["instructions"],
                "difficulty": move["difficulty"],
            })

    # Progressive muscle relaxation cool-down
    day_exercises.append({
        "name_en": "Progressive Muscle Relaxation",
        "name_ru": "Прогрессивная мышечная релаксация",
        "type": "flexibility",
        "duration_mins": 10,
        "instructions_en": "Lie down comfortably. Starting from the feet, tense each muscle group for 5 seconds then release for 20 seconds. Work upward through legs, abdomen, chest, arms, and face.",
        "instructions_ru": "Лягте удобно. Начиная со стоп, напрягайте каждую группу мышц на 5 секунд, затем расслабляйте на 20 секунд. Двигайтесь вверх через ноги, живот, грудь, руки и лицо.",
    })

    return day_exercises


def _general_health_day(
    day_num: int,
    age_group: str,
    exercises: list,
    time_per_session: int,
    equipment: list[str],
) -> list[dict]:
    """
    General health: balanced mix of cardio, strength, and flexibility/tai chi.
    Every third day includes tai chi instead of plain stretching.
    """
    day_exercises: list[dict] = []

    # Cardio warm-up
    cardio = _bodyweight_fallback("cardio", 1)
    for c in cardio:
        c = c.copy()
        c["duration_mins"] = 10
    day_exercises.extend(cardio)

    # Strength block (3 exercises)
    db_ex = _pick_exercises(exercises, ex_type="strength", count=3)
    day_exercises.extend(_resolve_exercises(db_ex, sets=3, reps=12))

    # Cool-down: tai chi every 3rd day, otherwise stretching
    if day_num % 3 == 0 and TAI_CHI_MOVES:
        sample_pool = TAI_CHI_MOVES[:12]  # First 12 are beginner/intermediate
        selected = random.sample(sample_pool, min(3, len(sample_pool)))
        for move in selected:
            day_exercises.append({
                "name_en": move["name_en"],
                "name_ru": move["name_ru"],
                "type": "tai_chi",
                "duration_mins": move["duration_mins"],
                "instructions": move["instructions"],
            })
    else:
        stretches = _bodyweight_fallback("flexibility", 2)
        day_exercises.extend(stretches)

    return day_exercises


# ---------------------------------------------------------------------------
# Exercise selection helpers
# ---------------------------------------------------------------------------
def _pick_exercises(
    exercises: list,
    body_part: str | None = None,
    ex_type: str | None = None,
    difficulty: str | None = None,
    count: int = 3,
) -> list:
    """
    Filter DB Exercise objects and return up to `count` random ones.
    Falls back to bodyweight exercises if the DB has no matches.
    """
    filtered = list(exercises)

    if body_part:
        filtered = [
            e for e in filtered
            if e.body_part and body_part.lower() in e.body_part.lower()
        ]
    if ex_type:
        filtered = [e for e in filtered if e.exercise_type == ex_type]
    if difficulty:
        filtered = [e for e in filtered if e.difficulty == difficulty]

    if not filtered:
        return _bodyweight_fallback(ex_type or "strength", count)

    return random.sample(filtered, min(count, len(filtered)))


def _resolve_exercises(
    db_result: list,
    sets: int = 3,
    reps: int = 12,
) -> list[dict]:
    """
    Normalize a list that may contain either Exercise ORM objects or already-dicts
    (from _bodyweight_fallback) into plain dicts suitable for plan_json.
    """
    out: list[dict] = []
    for item in db_result:
        if isinstance(item, dict):
            d = item.copy()
            if "sets" not in d and "duration_mins" not in d:
                d["sets"] = sets
                d["reps"] = reps
            out.append(d)
        else:
            # ORM Exercise object
            d: dict = {
                "name_en": item.name_en,
                "name_ru": item.name_ru or item.name_en,
                "type": item.exercise_type or "strength",
                "body_part": item.body_part,
                "equipment": item.equipment,
                "difficulty": item.difficulty,
                "sets": sets,
                "reps": reps,
            }
            if item.instructions:
                d["instructions"] = item.instructions
            out.append(d)
    return out


def _bodyweight_fallback(ex_type: str, count: int) -> list[dict]:
    """
    Hardcoded bodyweight exercises returned when the DB has no matching records.
    All exercises include both English and Russian names and are fully equipment-free.
    """
    library: dict[str, list[dict]] = {
        "strength": [
            {
                "name_en": "Push-ups",
                "name_ru": "Отжимания от пола",
                "type": "strength",
                "body_part": "chest",
                "sets": 3,
                "reps": 12,
                "instructions_en": "Start in a high plank. Lower chest to floor, then press back up. Keep body straight.",
                "instructions_ru": "Примите упор лёжа. Опустите грудь к полу, затем выжмитесь вверх. Держите тело прямым.",
            },
            {
                "name_en": "Squats",
                "name_ru": "Приседания",
                "type": "strength",
                "body_part": "legs",
                "sets": 3,
                "reps": 15,
                "instructions_en": "Stand feet shoulder-width apart. Sit hips back and down to parallel, then drive up through heels.",
                "instructions_ru": "Встаньте на ширину плеч. Отведите бёдра назад и вниз до параллели, затем поднимитесь через пятки.",
            },
            {
                "name_en": "Reverse Lunges",
                "name_ru": "Обратные выпады",
                "type": "strength",
                "body_part": "legs",
                "sets": 3,
                "reps": 12,
                "instructions_en": "Step one foot back and lower the rear knee toward the floor. Return to standing. Alternate legs.",
                "instructions_ru": "Шагните одной ногой назад и опустите заднее колено к полу. Вернитесь в исходное положение. Чередуйте ноги.",
            },
            {
                "name_en": "Plank Hold",
                "name_ru": "Статическая планка",
                "type": "strength",
                "body_part": "core",
                "duration_mins": 1,
                "instructions_en": "Hold a forearm plank with body in a straight line from head to heels. Brace the abs and glutes.",
                "instructions_ru": "Удерживайте планку на предплечьях, тело — прямая линия от головы до пяток. Напрягите пресс и ягодицы.",
            },
            {
                "name_en": "Glute Bridges",
                "name_ru": "Ягодичный мостик",
                "type": "strength",
                "body_part": "glutes",
                "sets": 3,
                "reps": 15,
                "instructions_en": "Lie on back with knees bent. Drive hips up by squeezing glutes, hold 2 seconds at top, lower.",
                "instructions_ru": "Лягте на спину, колени согнуты. Поднимите бёдра, сжимая ягодицы, удержите 2 секунды, опустите.",
            },
            {
                "name_en": "Tricep Dips",
                "name_ru": "Обратные отжимания на трицепс",
                "type": "strength",
                "body_part": "arms",
                "sets": 3,
                "reps": 12,
                "instructions_en": "Place hands on a chair behind you. Lower body by bending elbows to 90°, then press back up.",
                "instructions_ru": "Поставьте руки на стул сзади. Опуститесь, сгибая локти до 90°, затем поднимитесь.",
            },
            {
                "name_en": "Superman Hold",
                "name_ru": "Упражнение Супермен",
                "type": "strength",
                "body_part": "back",
                "sets": 3,
                "reps": 12,
                "instructions_en": "Lie face down. Simultaneously lift arms, chest, and legs off floor. Hold 2 seconds. Lower slowly.",
                "instructions_ru": "Лягте лицом вниз. Одновременно поднимите руки, грудь и ноги от пола. Задержите на 2 секунды.",
            },
            {
                "name_en": "Burpees",
                "name_ru": "Бёрпи",
                "type": "cardio",
                "body_part": "full_body",
                "sets": 3,
                "reps": 8,
                "instructions_en": "Stand, drop to plank, do a push-up, jump feet to hands, then leap up with arms overhead.",
                "instructions_ru": "Встаньте, примите упор лёжа, сделайте отжимание, прыжком подтяните ноги к рукам, выпрыгните вверх.",
            },
        ],
        "cardio": [
            {
                "name_en": "Jumping Jacks",
                "name_ru": "Прыжки ноги врозь-вместе",
                "type": "cardio",
                "body_part": "full_body",
                "duration_mins": 5,
                "instructions_en": "Jump feet apart while raising arms overhead, then jump feet together while lowering arms. Continuous rhythm.",
                "instructions_ru": "Прыгайте, расставляя ноги и поднимая руки над головой, затем сводите ноги и опускайте руки. Непрерывный ритм.",
            },
            {
                "name_en": "High Knees",
                "name_ru": "Высокие колени",
                "type": "cardio",
                "body_part": "legs",
                "duration_mins": 3,
                "instructions_en": "Run in place, driving knees up to hip height alternately. Pump arms naturally. Keep a fast pace.",
                "instructions_ru": "Бегите на месте, поднимая колени до уровня бёдер. Работайте руками. Поддерживайте быстрый темп.",
            },
            {
                "name_en": "Brisk Walking",
                "name_ru": "Быстрая ходьба",
                "type": "cardio",
                "body_part": "full_body",
                "duration_mins": 20,
                "intensity": "moderate",
                "instructions_en": "Walk at a brisk pace where you can speak but feel slightly breathless. Swing arms naturally.",
                "instructions_ru": "Идите в быстром темпе — вы можете говорить, но слегка задыхаетесь. Естественно работайте руками.",
            },
            {
                "name_en": "Running in Place",
                "name_ru": "Бег на месте",
                "type": "cardio",
                "body_part": "legs",
                "duration_mins": 10,
                "instructions_en": "Run on the spot with light footsteps. Land softly on the balls of the feet. Maintain upright posture.",
                "instructions_ru": "Бегите на месте с лёгкими шагами. Мягко приземляйтесь на подушечки стоп. Держите прямую осанку.",
            },
            {
                "name_en": "Mountain Climbers",
                "name_ru": "Скалолаз",
                "type": "cardio",
                "body_part": "core",
                "duration_mins": 2,
                "instructions_en": "In high plank, drive knees to chest alternately in a running motion. Keep hips level. Move fast.",
                "instructions_ru": "В упоре лёжа поочерёдно подтягивайте колени к груди в беговом движении. Удерживайте бёдра ровно.",
            },
        ],
        "flexibility": [
            {
                "name_en": "Hamstring Stretch",
                "name_ru": "Растяжка задней поверхности бедра",
                "type": "flexibility",
                "body_part": "legs",
                "duration_mins": 2,
                "instructions_en": "Sit on the floor, one leg extended. Reach toward the toes of the extended leg. Hold 30 seconds each side.",
                "instructions_ru": "Сядьте на пол, одна нога вытянута. Потянитесь к носку вытянутой ноги. Удержите 30 секунд с каждой стороны.",
            },
            {
                "name_en": "Cat-Cow Stretch",
                "name_ru": "Кошка-корова",
                "type": "flexibility",
                "body_part": "back",
                "duration_mins": 2,
                "instructions_en": "On hands and knees: arch back up (cat) on exhale, dip back down (cow) on inhale. Flow slowly 10 times.",
                "instructions_ru": "На четвереньках: на выдохе выгните спину вверх (кошка), на вдохе — вниз (корова). Медленно 10 раз.",
            },
            {
                "name_en": "Child's Pose",
                "name_ru": "Поза ребёнка",
                "type": "flexibility",
                "body_part": "back",
                "duration_mins": 2,
                "instructions_en": "Kneel and sit back on heels. Stretch arms forward on the floor and rest forehead down. Hold and breathe.",
                "instructions_ru": "Встаньте на колени и сядьте на пятки. Вытяните руки вперёд по полу, лоб — вниз. Удерживайте и дышите.",
            },
            {
                "name_en": "Seated Forward Bend",
                "name_ru": "Наклон вперёд сидя",
                "type": "flexibility",
                "body_part": "legs",
                "duration_mins": 2,
                "instructions_en": "Sit with both legs extended. Hinge forward from the hips (not waist) reaching hands toward feet. Hold 30 seconds.",
                "instructions_ru": "Сядьте с вытянутыми ногами. Наклонитесь вперёд от тазобедренных суставов, тянитесь руками к стопам. Удержите 30 секунд.",
            },
            {
                "name_en": "Pigeon Pose (Hip Opener)",
                "name_ru": "Поза голубя (раскрытие бедра)",
                "type": "flexibility",
                "body_part": "hips",
                "duration_mins": 3,
                "instructions_en": "From high plank, bring right knee forward and place it behind right wrist. Extend left leg back. Fold forward. Hold 60 seconds each side.",
                "instructions_ru": "Из упора лёжа подтяните правое колено к правому запястью. Вытяните левую ногу назад. Наклонитесь вперёд. Удержите 60 секунд на сторону.",
            },
        ],
    }

    pool = library.get(ex_type, library["strength"])
    # If count exceeds pool size, allow repeats by cycling
    if count > len(pool):
        return (pool * ((count // len(pool)) + 1))[:count]
    return random.sample(pool, count)
