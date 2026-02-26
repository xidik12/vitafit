"""Exercise plan generation — personalized weekly workout plans."""
import json
import logging
import math
import random
from pathlib import Path

from sqlalchemy import select

from app.database import (
    async_session, UserProfile, Exercise, ExercisePlan,
    WorkoutSession, WorkoutSetLog,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Load exercise data files at module level
# ---------------------------------------------------------------------------
_data_dir = Path(__file__).parent.parent / "data"


def _load_json(filename: str) -> list[dict]:
    path = _data_dir / filename
    if path.exists():
        with open(path, encoding="utf-8") as _f:
            data = json.load(_f)
        logger.info(f"Loaded {len(data)} entries from {filename}")
        return data
    logger.warning(f"{filename} not found at {path}")
    return []


TAI_CHI_MOVES: list[dict] = _load_json("tai_chi_moves.json")
YOGA_POSES: list[dict] = _load_json("yoga_poses.json")
PILATES_MOVES: list[dict] = _load_json("pilates_moves.json")
STRETCHING_ROUTINES: list[dict] = _load_json("stretching_routines.json")
BODYWEIGHT_EXERCISES: list[dict] = _load_json("bodyweight_exercises.json")

# ---------------------------------------------------------------------------
# Phase 9: Warm-up / Cool-down classification
# ---------------------------------------------------------------------------
# Stretching routines that involve movement/circles/rolls are classified as
# dynamic (suitable for warm-up); the rest are static (suitable for cool-down).
_DYNAMIC_KEYWORDS = {
    "circles", "circle", "rolls", "roll", "cat-cow", "cat cow", "windmill",
    "hip circles", "ankle circles", "shrugs", "world's greatest",
}


def _is_dynamic_stretch(stretch: dict) -> bool:
    """Heuristic: stretches with movement-based keywords are dynamic."""
    name_lower = (stretch.get("name_en") or "").lower()
    instructions_lower = (stretch.get("instructions") or "").lower()
    for kw in _DYNAMIC_KEYWORDS:
        if kw in name_lower or kw in instructions_lower:
            return True
    # Short-duration stretches with "sides" and movement cues
    if stretch.get("duration_secs", 0) <= 30 and any(
        w in instructions_lower for w in ("rotate", "swing", "flow", "circle", "roll")
    ):
        return True
    return False


# Pre-classify at module load
_DYNAMIC_STRETCHES: list[dict] = [s for s in STRETCHING_ROUTINES if _is_dynamic_stretch(s)]
_STATIC_STRETCHES: list[dict] = [s for s in STRETCHING_ROUTINES if not _is_dynamic_stretch(s)]

# Body-region to broad muscle group mapping for warm-up/cool-down filtering
_BODY_PART_TO_REGION: dict[str, list[str]] = {
    "chest": ["upper_body"],
    "back": ["upper_body", "core_back"],
    "shoulders": ["upper_body"],
    "arms": ["upper_body"],
    "legs": ["lower_body"],
    "core": ["core_back"],
    "glutes": ["lower_body"],
    "full_body": ["upper_body", "lower_body", "core_back", "full_body"],
    "hips": ["lower_body"],
}


def _calculate_sleep_hours(bedtime: str | None, waketime: str | None) -> float | None:
    """Calculate approximate sleep hours from HH:MM strings."""
    if not bedtime or not waketime:
        return None
    try:
        bed_h, bed_m = map(int, bedtime.split(":"))
        wake_h, wake_m = map(int, waketime.split(":"))
        bed_total = bed_h * 60 + bed_m
        wake_total = wake_h * 60 + wake_m
        if wake_total <= bed_total:
            # Crossed midnight (e.g. 23:00 → 07:00)
            diff = (24 * 60 - bed_total) + wake_total
        else:
            # Same-day (e.g. 01:00 → 08:00)
            diff = wake_total - bed_total
        return diff / 60.0
    except (ValueError, AttributeError):
        return None


def _get_warm_up(primary_body_parts: list[str], count: int = 4) -> list[dict]:
    """Select dynamic stretches relevant to the day's primary muscle groups."""
    # Determine relevant body regions
    regions: set[str] = set()
    for bp in primary_body_parts:
        regions.update(_BODY_PART_TO_REGION.get(bp.lower(), ["full_body"]))
    if not regions:
        regions = {"upper_body", "lower_body", "core_back", "full_body"}

    # Filter dynamic stretches by region; fall back to all dynamic stretches
    relevant = [
        s for s in _DYNAMIC_STRETCHES
        if s.get("body_region", "full_body") in regions
    ]
    if len(relevant) < count:
        # Add any remaining dynamic stretches not already selected
        remaining = [s for s in _DYNAMIC_STRETCHES if s not in relevant]
        relevant.extend(remaining)
    if not relevant:
        # Ultimate fallback: use all stretching routines
        relevant = STRETCHING_ROUTINES[:count]

    picks = random.sample(relevant, min(count, len(relevant)))
    result = []
    for s in picks:
        duration_mins = max(1, round(s.get("duration_secs", 30) / 60))
        result.append({
            "name_en": s["name_en"],
            "name_ru": s.get("name_ru", s["name_en"]),
            "type": "warm_up",
            "stretch_type": "dynamic",
            "duration_mins": duration_mins,
            "instructions": s.get("instructions", ""),
            "body_region": s.get("body_region", ""),
            "tips": s.get("tips", ""),
        })
    return result


def _get_cool_down(primary_body_parts: list[str], count: int = 4) -> list[dict]:
    """Select static stretches relevant to the day's primary muscle groups."""
    regions: set[str] = set()
    for bp in primary_body_parts:
        regions.update(_BODY_PART_TO_REGION.get(bp.lower(), ["full_body"]))
    if not regions:
        regions = {"upper_body", "lower_body", "core_back", "full_body"}

    relevant = [
        s for s in _STATIC_STRETCHES
        if s.get("body_region", "full_body") in regions
    ]
    if len(relevant) < count:
        remaining = [s for s in _STATIC_STRETCHES if s not in relevant]
        relevant.extend(remaining)
    if not relevant:
        relevant = STRETCHING_ROUTINES[:count]

    picks = random.sample(relevant, min(count, len(relevant)))
    result = []
    for s in picks:
        duration_mins = max(1, round(s.get("duration_secs", 30) / 60))
        result.append({
            "name_en": s["name_en"],
            "name_ru": s.get("name_ru", s["name_en"]),
            "type": "cool_down",
            "stretch_type": "static",
            "duration_mins": duration_mins,
            "instructions": s.get("instructions", ""),
            "body_region": s.get("body_region", ""),
            "tips": s.get("tips", ""),
        })
    return result


def _extract_day_body_parts(exercises: list[dict]) -> list[str]:
    """Extract the primary body parts from a day's exercise list."""
    parts: set[str] = set()
    for ex in exercises:
        bp = ex.get("body_part", "")
        if bp:
            parts.add(bp.lower())
    return list(parts) if parts else ["full_body"]


# ---------------------------------------------------------------------------
# Phase 2: Progressive Overload
# ---------------------------------------------------------------------------
async def get_progression_suggestions(user_id: int) -> list[dict]:
    """
    Analyze recent workout logs and suggest progressive overload adjustments.

    For each exercise, looks at the last 2 completed sessions. If the user
    completed all planned reps for 2+ consecutive sessions at the same weight,
    suggests:
      - +2.5 kg if weight was used
      - +2 reps if bodyweight exercise
    """
    suggestions: list[dict] = []

    async with async_session() as session:
        # Get all set logs for the user, ordered by session date desc
        stmt = (
            select(
                WorkoutSetLog.exercise_name,
                WorkoutSetLog.set_number,
                WorkoutSetLog.reps_planned,
                WorkoutSetLog.reps_done,
                WorkoutSetLog.weight_kg,
                WorkoutSetLog.completed,
                WorkoutSession.date,
                WorkoutSession.id.label("session_id"),
            )
            .join(WorkoutSession, WorkoutSetLog.session_id == WorkoutSession.id)
            .where(WorkoutSession.user_id == user_id)
            .where(WorkoutSession.completed == True)  # noqa: E712
            .order_by(WorkoutSetLog.exercise_name, WorkoutSession.date.desc())
        )
        result = await session.execute(stmt)
        rows = result.all()

    if not rows:
        return suggestions

    # Group by exercise_name
    exercises_grouped: dict[str, list] = {}
    for row in rows:
        name = row.exercise_name
        if name not in exercises_grouped:
            exercises_grouped[name] = []
        exercises_grouped[name].append(row)

    for exercise_name, all_sets in exercises_grouped.items():
        # Group sets by session_id to identify distinct sessions
        session_sets: dict[int, list] = {}
        for s in all_sets:
            sid = s.session_id
            if sid not in session_sets:
                session_sets[sid] = []
            session_sets[sid].append(s)

        # Order sessions by date desc, take last 2
        sorted_sessions = sorted(
            session_sets.values(),
            key=lambda sets: sets[0].date,
            reverse=True,
        )
        if len(sorted_sessions) < 2:
            continue  # Need at least 2 sessions to evaluate

        last_two = sorted_sessions[:2]

        # Check if ALL sets were completed in both sessions
        both_completed = True
        weights_used: list[float | None] = []
        max_reps_done: list[int] = []

        for session_set_list in last_two:
            for s in session_set_list:
                if not s.completed:
                    both_completed = False
                    break
                if s.reps_planned and s.reps_done and s.reps_done < s.reps_planned:
                    both_completed = False
                    break
            if not both_completed:
                break
            # Track weights and reps
            session_weights = [s.weight_kg for s in session_set_list if s.weight_kg is not None]
            session_reps = [s.reps_done for s in session_set_list if s.reps_done is not None]
            weights_used.append(max(session_weights) if session_weights else None)
            max_reps_done.append(max(session_reps) if session_reps else 0)

        if not both_completed:
            continue

        # Both sessions completed all planned reps — suggest progression
        # Check if same weight was used across both sessions
        w1 = weights_used[0] if len(weights_used) > 0 else None
        w2 = weights_used[1] if len(weights_used) > 1 else None

        if w1 is not None and w2 is not None and w1 == w2:
            # Weighted exercise: suggest +2.5 kg
            suggestions.append({
                "exercise_name": exercise_name,
                "suggested_weight_kg": round(w1 + 2.5, 1),
                "suggested_reps": None,
                "reason": (
                    f"Completed all planned reps at {w1}kg for 2 consecutive "
                    f"sessions. Ready to increase weight by 2.5kg."
                ),
            })
        elif w1 is None and w2 is None:
            # Bodyweight exercise: suggest +2 reps
            current_reps = max_reps_done[0] if max_reps_done else 12
            suggestions.append({
                "exercise_name": exercise_name,
                "suggested_weight_kg": None,
                "suggested_reps": current_reps + 2,
                "reason": (
                    f"Completed all planned reps ({current_reps}) for 2 consecutive "
                    f"sessions. Ready to add 2 more reps."
                ),
            })
        elif w1 is not None and w2 is not None:
            # Weights differ but both sessions complete — suggest increase from higher
            higher_w = max(w1, w2)
            suggestions.append({
                "exercise_name": exercise_name,
                "suggested_weight_kg": round(higher_w + 2.5, 1),
                "suggested_reps": None,
                "reason": (
                    f"Completed all planned reps in last 2 sessions "
                    f"(weights: {w1}kg, {w2}kg). Ready to increase to {round(higher_w + 2.5, 1)}kg."
                ),
            })

    return suggestions


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
    stress_level = (profile.stress_level or "medium").lower().strip()
    job_type = (profile.job_type or "").lower().strip()
    sleep_hours = _calculate_sleep_hours(profile.sleep_bedtime, profile.sleep_waketime)

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

    # Phase 5: Equipment filtering — restrict DB exercises to those
    # matching the user's equipment OR "body only"
    if equipment:
        equipment_set = set(equipment)
        exercises = [
            e for e in exercises
            if not e.equipment
            or e.equipment.lower().strip() in ("body only", "body weight", "bodyweight", "none", "")
            or e.equipment.lower().strip() in equipment_set
        ]
        logger.info(
            f"User {user_id}: equipment filter applied ({equipment_set}), "
            f"{len(exercises)} exercises remain"
        )

    # Phase 5: Age-specific filtering (65+)
    if age >= 65:
        _plyometric_keywords = {"plyometric", "jump", "box jump", "jumping", "plyo"}
        exercises = [
            e for e in exercises
            if not any(kw in (e.name_en or "").lower() for kw in _plyometric_keywords)
        ]
        # Prefer lower difficulty
        beginner_exercises = [e for e in exercises if e.difficulty == "beginner"]
        if len(beginner_exercises) >= 10:
            exercises = beginner_exercises
        logger.info(f"User {user_id}: age 65+ filter, {len(exercises)} exercises remain")

    # Build profile context dict for smart adjustments (passed to day builders)
    profile_ctx = {
        "stress_level": stress_level,
        "job_type": job_type,
        "sleep_hours": sleep_hours,
        "age": age,
    }

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
            profile_ctx=profile_ctx,
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
    profile_ctx: dict | None = None,
) -> dict:
    """Route to goal-specific plan builder with smart adjustments."""
    ctx = profile_ctx or {}
    stress_level = ctx.get("stress_level", "medium")
    job_type = ctx.get("job_type", "")
    sleep_hours = ctx.get("sleep_hours")

    plan = {
        "user_id": user_id,
        "goal": goal,
        "age_group": age_group,
        "total_days": 7,
        "workout_days": workout_days,
        "gentle": False,
        "days": [],
    }

    # Phase 5: stress/sleep notes attached to the plan
    if stress_level == "high":
        plan["stress_note"] = (
            "Your stress level is high — workout volume is reduced and "
            "yoga/stretching has been added to each session."
        )
    if sleep_hours is not None and sleep_hours < 6:
        plan["sleep_note"] = (
            f"You are getting ~{sleep_hours:.1f}h of sleep. Intensity and "
            f"sets have been reduced, and recovery exercises added."
        )

    for day_num in range(1, 8):
        if day_num > workout_days:
            plan["days"].append({
                "day": day_num,
                "type": "rest",
                "exercises": [],
                "warm_up": [],
                "cool_down": [],
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

        # --- Phase 5: Smart adjustments ---

        # Stress-aware: reduce exercises by ~20% and add yoga/stretching
        if stress_level == "high":
            original_count = len(day_exercises)
            reduced_count = max(2, math.ceil(original_count * 0.8))
            if len(day_exercises) > reduced_count:
                day_exercises = day_exercises[:reduced_count]
            # Add 1 yoga or stretching exercise for stress relief
            yoga_pool = [p for p in YOGA_POSES if p.get("difficulty") == "beginner"]
            if yoga_pool:
                pick = random.choice(yoga_pool)
                duration_mins = max(1, round(pick.get("duration_secs", 30) / 60))
                day_exercises.append({
                    "name_en": pick["name_en"],
                    "name_ru": pick.get("name_ru", pick["name_en"]),
                    "type": "yoga",
                    "duration_mins": duration_mins,
                    "instructions": pick.get("instructions", ""),
                    "difficulty": "beginner",
                    "note": "Added for stress relief",
                })

        # Sleep-aware: if < 6 hours, reduce sets and add recovery
        if sleep_hours is not None and sleep_hours < 6:
            for ex in day_exercises:
                if "sets" in ex and ex["sets"] > 2:
                    ex["sets"] = max(2, ex["sets"] - 1)
            # Add a recovery/stretching exercise
            recovery_pool = [
                s for s in STRETCHING_ROUTINES
                if s.get("difficulty") == "beginner"
            ]
            if recovery_pool:
                pick = random.choice(recovery_pool)
                duration_mins = max(1, round(pick.get("duration_secs", 30) / 60))
                day_exercises.append({
                    "name_en": pick["name_en"],
                    "name_ru": pick.get("name_ru", pick["name_en"]),
                    "type": "flexibility",
                    "duration_mins": duration_mins,
                    "instructions": pick.get("instructions", ""),
                    "difficulty": "beginner",
                    "note": "Added for recovery (low sleep)",
                })

        # Job-type adjustment
        if job_type == "physical":
            # Reduce lower-body volume: remove one leg exercise, add upper body
            leg_indices = [
                i for i, ex in enumerate(day_exercises)
                if ex.get("body_part", "").lower() in ("legs", "glutes", "hamstrings", "quadriceps")
            ]
            if leg_indices:
                day_exercises.pop(leg_indices[-1])  # Remove last leg exercise
                # Add an upper body exercise from bodyweight pool
                upper_pool = [
                    e for e in BODYWEIGHT_EXERCISES
                    if e.get("body_part", "").lower() in ("chest", "arms", "shoulders", "back")
                ]
                if not upper_pool:
                    upper_pool = [
                        e for e in BODYWEIGHT_EXERCISES
                        if e.get("category") in ("push", "pull")
                    ]
                if upper_pool:
                    pick = random.choice(upper_pool)
                    day_exercises.append({
                        "name_en": pick["name_en"],
                        "name_ru": pick.get("name_ru", pick["name_en"]),
                        "type": "strength",
                        "body_part": pick.get("body_part", "upper_body"),
                        "difficulty": pick.get("difficulty", "beginner"),
                        "sets": 3,
                        "reps": pick.get("reps", 12),
                        "instructions": pick.get("instructions", ""),
                        "note": "Added to compensate for physical job (lower-body reduced)",
                    })
        elif job_type == "sedentary":
            # Add mobility/flexibility exercise for desk workers
            mobility_pool = [
                s for s in STRETCHING_ROUTINES
                if s.get("body_region") in ("upper_body", "core_back")
                and s.get("difficulty") == "beginner"
            ]
            if not mobility_pool:
                mobility_pool = [s for s in STRETCHING_ROUTINES if s.get("difficulty") == "beginner"]
            if mobility_pool:
                pick = random.choice(mobility_pool)
                duration_mins = max(1, round(pick.get("duration_secs", 30) / 60))
                day_exercises.append({
                    "name_en": pick["name_en"],
                    "name_ru": pick.get("name_ru", pick["name_en"]),
                    "type": "flexibility",
                    "duration_mins": duration_mins,
                    "instructions": pick.get("instructions", ""),
                    "difficulty": "beginner",
                    "body_region": pick.get("body_region", ""),
                    "note": "Added for mobility (sedentary job)",
                })

        # --- Phase 9: Warm-up / Cool-down ---
        body_parts = _extract_day_body_parts(day_exercises)
        warm_up = _get_warm_up(body_parts, count=random.randint(3, 5))
        cool_down = _get_cool_down(body_parts, count=random.randint(3, 5))

        plan["days"].append({
            "day": day_num,
            "type": "workout",
            "warm_up": warm_up,
            "exercises": day_exercises,
            "cool_down": cool_down,
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
    Cardio uses bodyweight_exercises.json when available.
    Cool-down uses stretching_routines.json when available.
    Alternates muscle group targets each day to ensure full-body coverage.
    """
    day_exercises: list[dict] = []

    # --- Cardio warm-up (prefer bodyweight_exercises.json cardio category) ---
    cardio_mins = max(10, time_per_session // 3)
    bw_cardio = [e for e in BODYWEIGHT_EXERCISES if e.get("category") == "cardio"]
    if bw_cardio:
        picks = random.sample(bw_cardio, min(2, len(bw_cardio)))
        each_mins = max(1, cardio_mins // len(picks))
        for c in picks:
            day_exercises.append({
                "name_en": c["name_en"],
                "name_ru": c["name_ru"],
                "type": "cardio",
                "duration_mins": each_mins,
                "instructions": c.get("instructions", ""),
                "difficulty": c.get("difficulty", "beginner"),
            })
    else:
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
    resolved = _resolve_exercises(db_ex, sets=sets, reps=reps)

    # Supplement with bodyweight_exercises.json if DB returned too few
    if len(resolved) < 3 and BODYWEIGHT_EXERCISES:
        bw_strength = [
            e for e in BODYWEIGHT_EXERCISES
            if e.get("body_part", "").lower() == target or e.get("category") in ("push", "pull", "legs", "core")
        ]
        if not bw_strength:
            bw_strength = BODYWEIGHT_EXERCISES
        already_names = {r.get("name_en") for r in resolved}
        bw_strength = [e for e in bw_strength if e["name_en"] not in already_names]
        needed = 3 - len(resolved)
        picks = random.sample(bw_strength, min(needed, len(bw_strength)))
        for e in picks:
            resolved.append({
                "name_en": e["name_en"],
                "name_ru": e["name_ru"],
                "type": "strength",
                "body_part": e.get("body_part", ""),
                "difficulty": e.get("difficulty", "beginner"),
                "sets": sets,
                "reps": e.get("reps", reps),
                "instructions": e.get("instructions", ""),
            })
    day_exercises.extend(resolved)

    # --- Cool-down stretch (prefer stretching_routines.json) ---
    pool = [s for s in STRETCHING_ROUTINES if s.get("difficulty") == "beginner"]
    if not pool:
        pool = STRETCHING_ROUTINES
    if pool:
        picks = random.sample(pool, min(2, len(pool)))
        for stretch in picks:
            duration_mins = max(1, round(stretch.get("duration_secs", 30) / 60))
            day_exercises.append({
                "name_en": stretch["name_en"],
                "name_ru": stretch["name_ru"],
                "type": "flexibility",
                "duration_mins": duration_mins,
                "instructions": stretch.get("instructions", ""),
                "body_region": stretch.get("body_region", ""),
            })
    else:
        day_exercises.extend(_bodyweight_fallback("flexibility", 2))

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
    Bodyweight_exercises.json used to supplement DB results.
    Core days include pilates moves for targeted core work.
    """
    # Push/Pull/Legs/Shoulders/Arms/Legs2/Core split
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

    # Supplement with bodyweight_exercises.json if DB returned fewer than 4
    if len(day_exercises) < 4 and BODYWEIGHT_EXERCISES:
        category_map = {
            "chest": ("push",),
            "back": ("pull",),
            "legs": ("legs",),
            "shoulders": ("push",),
            "arms": ("push", "pull"),
            "core": ("core",),
            "full_body": ("push", "pull", "legs", "core", "full_body"),
        }
        cats = category_map.get(target, ("push", "pull", "legs", "core"))
        bw_pool = [e for e in BODYWEIGHT_EXERCISES if e.get("category") in cats]
        if not bw_pool:
            bw_pool = BODYWEIGHT_EXERCISES
        already_names = {d.get("name_en") for d in day_exercises}
        bw_pool = [e for e in bw_pool if e["name_en"] not in already_names]
        needed = 4 - len(day_exercises)
        picks = random.sample(bw_pool, min(needed, len(bw_pool)))
        for e in picks:
            day_exercises.append({
                "name_en": e["name_en"],
                "name_ru": e["name_ru"],
                "type": "strength",
                "body_part": e.get("body_part", ""),
                "difficulty": e.get("difficulty", "beginner"),
                "sets": sets,
                "reps": e.get("reps", reps),
                "instructions": e.get("instructions", ""),
            })
    elif len(day_exercises) < 4:
        # Last resort: hardcoded fallback
        fallback = _bodyweight_fallback("strength", 4 - len(day_exercises))
        for ex in fallback:
            ex = ex.copy()
            ex["sets"] = sets
            ex["reps"] = reps
        day_exercises.extend(fallback)

    # Core day: append pilates core finisher (2 moves)
    if target == "core" and PILATES_MOVES:
        pilates_core = [
            p for p in PILATES_MOVES
            if p.get("category") == "core" and p.get("difficulty") in ("beginner", "intermediate")
        ]
        if not pilates_core:
            pilates_core = [p for p in PILATES_MOVES if p.get("difficulty") == "beginner"]
        if pilates_core:
            picks = random.sample(pilates_core, min(2, len(pilates_core)))
            for move in picks:
                day_exercises.append({
                    "name_en": move["name_en"],
                    "name_ru": move["name_ru"],
                    "type": "pilates",
                    "sets": move.get("sets", 1),
                    "reps": move.get("reps", 8),
                    "instructions": move.get("instructions", ""),
                    "difficulty": move.get("difficulty", "beginner"),
                    "breathing": move.get("breathing", ""),
                })

    return day_exercises


def _flexibility_day(
    day_num: int,
    age_group: str,
    time_per_session: int,
) -> list[dict]:
    """
    Flexibility: cycles through tai chi, yoga, and stretching days.
    Day pattern (mod 3): 1=tai chi, 2=yoga, 0=stretching routines.
    Seniors get beginner-only content; young/middle get intermediate too.
    """
    day_exercises: list[dict] = []
    allowed_difficulties = (
        ["beginner"] if age_group == "senior"
        else ["beginner", "intermediate"]
    )

    pattern = day_num % 3

    if pattern == 1:
        # Tai chi day
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

    elif pattern == 2:
        # Yoga day — pull from loaded yoga_poses.json
        pool = [p for p in YOGA_POSES if p["difficulty"] in allowed_difficulties]
        if not pool:
            pool = YOGA_POSES  # fall back to full list
        count = min(6, len(pool))
        selected = random.sample(pool, count) if pool else []
        for pose in selected:
            duration_mins = max(1, round(pose.get("duration_secs", 30) / 60))
            day_exercises.append({
                "name_en": pose["name_en"],
                "name_ru": pose["name_ru"],
                "type": "yoga",
                "duration_mins": duration_mins,
                "instructions": pose.get("instructions", ""),
                "difficulty": pose.get("difficulty", "beginner"),
                "benefits": pose.get("benefits", ""),
            })
        # Close with breathing exercise
        day_exercises.append({
            "name_en": "Diaphragmatic Deep Breathing",
            "name_ru": "Диафрагмальное глубокое дыхание",
            "type": "flexibility",
            "duration_mins": 5,
            "instructions_en": "Lie on your back. Place one hand on the chest, one on the belly. Breathe deeply so only the belly hand rises. 5 seconds in, hold 2, 5 seconds out.",
            "instructions_ru": "Лягте на спину. Одну руку положите на грудь, другую на живот. Дышите глубоко так, чтобы поднималась только рука на животе. 5 секунд вдох, задержка 2, 5 секунд выдох.",
        })

    else:
        # Stretching routines day — pull from loaded stretching_routines.json
        pool = [s for s in STRETCHING_ROUTINES if s.get("difficulty") in allowed_difficulties]
        if not pool:
            pool = STRETCHING_ROUTINES
        count = min(5, len(pool))
        selected = random.sample(pool, count) if pool else []
        for stretch in selected:
            duration_mins = max(1, round(stretch.get("duration_secs", 30) / 60))
            day_exercises.append({
                "name_en": stretch["name_en"],
                "name_ru": stretch["name_ru"],
                "type": "flexibility",
                "duration_mins": duration_mins,
                "instructions": stretch.get("instructions", ""),
                "difficulty": stretch.get("difficulty", "beginner"),
                "body_region": stretch.get("body_region", ""),
            })
        # Fallback if stretching_routines.json was empty
        if not day_exercises:
            day_exercises.extend(_bodyweight_fallback("flexibility", 4))

    return day_exercises


def _stress_relief_day(
    day_num: int,
    age_group: str,
    time_per_session: int,
) -> list[dict]:
    """
    Stress relief: mindful walking + alternates tai chi / yoga / stretching + relaxation.
    Always calm, low-intensity, meditative in nature.
    Day pattern (mod 3): 1=tai chi, 2=yoga, 0=stretching.
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

    pattern = day_num % 3

    if pattern == 1:
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

    elif pattern == 2:
        # Restorative / beginner yoga (4 poses)
        restorative_categories = {"restorative", "supine", "seated"}
        pool = [
            p for p in YOGA_POSES
            if p.get("difficulty") == "beginner"
            and p.get("category") in restorative_categories
        ]
        if not pool:
            pool = [p for p in YOGA_POSES if p.get("difficulty") == "beginner"]
        if not pool:
            pool = YOGA_POSES
        count = min(4, len(pool))
        selected = random.sample(pool, count) if pool else []
        for pose in selected:
            duration_mins = max(1, round(pose.get("duration_secs", 30) / 60))
            day_exercises.append({
                "name_en": pose["name_en"],
                "name_ru": pose["name_ru"],
                "type": "yoga",
                "duration_mins": duration_mins,
                "instructions": pose.get("instructions", ""),
                "difficulty": pose.get("difficulty", "beginner"),
                "benefits": pose.get("benefits", ""),
            })

    else:
        # Gentle stretching (4 routines)
        pool = [s for s in STRETCHING_ROUTINES if s.get("difficulty") == "beginner"]
        if not pool:
            pool = STRETCHING_ROUTINES
        count = min(4, len(pool))
        selected = random.sample(pool, count) if pool else []
        for stretch in selected:
            duration_mins = max(1, round(stretch.get("duration_secs", 30) / 60))
            day_exercises.append({
                "name_en": stretch["name_en"],
                "name_ru": stretch["name_ru"],
                "type": "flexibility",
                "duration_mins": duration_mins,
                "instructions": stretch.get("instructions", ""),
                "difficulty": stretch.get("difficulty", "beginner"),
                "body_region": stretch.get("body_region", ""),
            })
        if not day_exercises:
            day_exercises.extend(_bodyweight_fallback("flexibility", 4))

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
    General health: balanced mix of cardio, strength (from bodyweight_exercises.json
    when DB is empty), and a rotating cool-down (tai chi / pilates core / stretching).
    Cool-down pattern (mod 3): 1=tai chi, 2=pilates core, 0=stretching routines.
    """
    day_exercises: list[dict] = []

    # Cardio warm-up — prefer bodyweight_exercises.json cardio, fall back to hardcoded
    bw_cardio = [e for e in BODYWEIGHT_EXERCISES if e.get("category") == "cardio"]
    if bw_cardio:
        cardio_pick = random.sample(bw_cardio, min(1, len(bw_cardio)))
        for c in cardio_pick:
            day_exercises.append({
                "name_en": c["name_en"],
                "name_ru": c["name_ru"],
                "type": "cardio",
                "duration_mins": 10,
                "instructions": c.get("instructions", ""),
                "difficulty": c.get("difficulty", "beginner"),
            })
    else:
        cardio = _bodyweight_fallback("cardio", 1)
        for c in cardio:
            c = c.copy()
            c["duration_mins"] = 10
        day_exercises.extend(cardio)

    # Strength block — try DB first, supplement/replace with bodyweight_exercises.json
    db_ex = _pick_exercises(exercises, ex_type="strength", count=3)
    resolved = _resolve_exercises(db_ex, sets=3, reps=12)
    if len(resolved) < 3 and BODYWEIGHT_EXERCISES:
        # Fill remaining slots from BODYWEIGHT_EXERCISES (strength/push/pull categories)
        bw_strength = [
            e for e in BODYWEIGHT_EXERCISES
            if e.get("category") in ("push", "pull", "legs", "core", "full_body")
        ]
        needed = 3 - len(resolved)
        already_names = {r.get("name_en") for r in resolved}
        bw_strength = [e for e in bw_strength if e["name_en"] not in already_names]
        if bw_strength:
            picks = random.sample(bw_strength, min(needed, len(bw_strength)))
            for e in picks:
                resolved.append({
                    "name_en": e["name_en"],
                    "name_ru": e["name_ru"],
                    "type": "strength",
                    "body_part": e.get("body_part", ""),
                    "difficulty": e.get("difficulty", "beginner"),
                    "sets": 3,
                    "reps": e.get("reps", 12),
                    "instructions": e.get("instructions", ""),
                })
    day_exercises.extend(resolved)

    # Cool-down rotation
    pattern = day_num % 3
    if pattern == 1 and TAI_CHI_MOVES:
        allowed = (
            ["beginner"] if age_group == "senior"
            else ["beginner", "intermediate"]
        )
        pool = [m for m in TAI_CHI_MOVES if m["difficulty"] in allowed][:12]
        selected = random.sample(pool, min(3, len(pool))) if pool else []
        for move in selected:
            day_exercises.append({
                "name_en": move["name_en"],
                "name_ru": move["name_ru"],
                "type": "tai_chi",
                "duration_mins": move["duration_mins"],
                "instructions": move["instructions"],
            })
    elif pattern == 2 and PILATES_MOVES:
        # Pilates core cool-down (beginner-friendly)
        core_pilates = [
            p for p in PILATES_MOVES
            if p.get("difficulty") == "beginner" and p.get("category") in ("core", "flexibility")
        ]
        if not core_pilates:
            core_pilates = [p for p in PILATES_MOVES if p.get("difficulty") == "beginner"]
        if not core_pilates:
            core_pilates = PILATES_MOVES
        selected = random.sample(core_pilates, min(3, len(core_pilates)))
        for move in selected:
            day_exercises.append({
                "name_en": move["name_en"],
                "name_ru": move["name_ru"],
                "type": "pilates",
                "sets": move.get("sets", 1),
                "reps": move.get("reps", 8),
                "instructions": move.get("instructions", ""),
                "difficulty": move.get("difficulty", "beginner"),
                "breathing": move.get("breathing", ""),
            })
    else:
        # Stretching routines cool-down
        pool = [s for s in STRETCHING_ROUTINES if s.get("difficulty") == "beginner"]
        if not pool:
            pool = STRETCHING_ROUTINES
        if pool:
            selected = random.sample(pool, min(2, len(pool)))
            for stretch in selected:
                duration_mins = max(1, round(stretch.get("duration_secs", 30) / 60))
                day_exercises.append({
                    "name_en": stretch["name_en"],
                    "name_ru": stretch["name_ru"],
                    "type": "flexibility",
                    "duration_mins": duration_mins,
                    "instructions": stretch.get("instructions", ""),
                })
        else:
            day_exercises.extend(_bodyweight_fallback("flexibility", 2))

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
