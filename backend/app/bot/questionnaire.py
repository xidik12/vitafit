"""Questionnaire FSM — collects user profile data in 6 modules."""
import json
import logging
from pathlib import Path

from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy import select

from app.database import async_session, User, UserProfile, QuestionnaireAnswer, UserStreak, ReminderSettings
from app.bot.i18n import t
from app.bot.keyboards import (
    consent_keyboard, main_keyboard, yes_no_keyboard,
    questionnaire_goals_keyboard, activity_level_keyboard,
    dietary_pref_keyboard, sex_keyboard,
)

logger = logging.getLogger(__name__)
router = Router()

# Load PAR-Q questions
_parq_path = Path(__file__).parent.parent / "data" / "parq_questions.json"
with open(_parq_path) as f:
    PARQ_QUESTIONS = json.load(f)


class QState(StatesGroup):
    # Language + consent
    consent = State()
    # PAR-Q (7 yes/no)
    parq = State()
    # Goals
    goal = State()
    # Body metrics
    sex = State()
    age = State()
    weight = State()
    height = State()
    activity_level = State()
    # Diet
    dietary_pref = State()
    allergies = State()
    # Sleep
    sleep_bedtime = State()
    sleep_waketime = State()
    # Lifestyle
    job_type = State()
    stress_level = State()
    equipment = State()
    time_per_week = State()


# ── Language selection ────────────────────────────────────────
@router.callback_query(F.data.startswith("lang:"))
async def on_language(callback: CallbackQuery, state: FSMContext):
    lang = callback.data.split(":")[1]
    await callback.answer()

    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == callback.from_user.id)
        )
        user = result.scalar_one_or_none()
        if user:
            user.language = lang
            await session.commit()

    await state.update_data(lang=lang)
    await callback.message.edit_text(
        t("language_set", lang),
    )
    await callback.message.answer(
        t("consent_prompt", lang),
        reply_markup=consent_keyboard(lang),
    )
    await state.set_state(QState.consent)


# ── Consent ──────────────────────────────────────────────────
@router.callback_query(F.data.startswith("consent:"), QState.consent)
async def on_consent(callback: CallbackQuery, state: FSMContext):
    choice = callback.data.split(":")[1]
    data = await state.get_data()
    lang = data.get("lang", "ru")
    await callback.answer()

    if choice == "no":
        await callback.message.edit_text(t("consent_declined", lang))
        await state.clear()
        return

    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == callback.from_user.id)
        )
        user = result.scalar_one_or_none()
        if user:
            user.consent_given = True
            await session.commit()

    await state.update_data(parq_index=0, parq_yes_count=0)
    q = PARQ_QUESTIONS[0]
    await callback.message.edit_text(
        f"1/7: {q[lang]}",
        reply_markup=yes_no_keyboard(lang),
    )
    await state.set_state(QState.parq)


# ── Start questionnaire from main menu ───────────────────────
@router.callback_query(F.data == "start_questionnaire")
async def on_start_questionnaire(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    # Check if user already has language set
    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == callback.from_user.id)
        )
        user = result.scalar_one_or_none()

    lang = user.language if user else "ru"

    if user and user.consent_given:
        # Skip consent, go straight to PAR-Q
        await state.update_data(lang=lang, parq_index=0, parq_yes_count=0)
        q = PARQ_QUESTIONS[0]
        await callback.message.edit_text(
            f"1/7: {q[lang]}",
            reply_markup=yes_no_keyboard(lang),
        )
        await state.set_state(QState.parq)
    else:
        await state.update_data(lang=lang)
        await callback.message.edit_text(
            t("consent_prompt", lang),
            reply_markup=consent_keyboard(lang),
        )
        await state.set_state(QState.consent)


# ── PAR-Q ────────────────────────────────────────────────────
@router.callback_query(F.data.startswith("answer:"), QState.parq)
async def on_parq_answer(callback: CallbackQuery, state: FSMContext):
    answer = callback.data.split(":")[1]
    data = await state.get_data()
    lang = data.get("lang", "ru")
    idx = data.get("parq_index", 0)
    yes_count = data.get("parq_yes_count", 0)
    await callback.answer()

    if answer == "yes":
        yes_count += 1

    # Save answer
    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == callback.from_user.id)
        )
        user = result.scalar_one_or_none()
        if user:
            qa = QuestionnaireAnswer(
                user_id=user.id,
                module="parq",
                question_key=PARQ_QUESTIONS[idx]["key"],
                answer_value=answer,
            )
            session.add(qa)
            await session.commit()

    idx += 1
    if idx < len(PARQ_QUESTIONS):
        await state.update_data(parq_index=idx, parq_yes_count=yes_count)
        q = PARQ_QUESTIONS[idx]
        await callback.message.edit_text(
            f"{idx + 1}/7: {q[lang]}",
            reply_markup=yes_no_keyboard(lang),
        )
    else:
        # PAR-Q complete
        parq_passed = yes_count == 0
        await state.update_data(parq_passed=parq_passed)
        if not parq_passed:
            await callback.message.edit_text(t("parq_warning", lang))

        # Move to Goals
        await callback.message.answer(
            _module_title("goals", lang),
            reply_markup=questionnaire_goals_keyboard(lang),
        )
        await state.set_state(QState.goal)


# ── Goals ────────────────────────────────────────────────────
@router.callback_query(F.data.startswith("goal:"), QState.goal)
async def on_goal(callback: CallbackQuery, state: FSMContext):
    goal = callback.data.split(":")[1]
    data = await state.get_data()
    lang = data.get("lang", "ru")
    await callback.answer()
    await state.update_data(goal=goal)

    # Move to Sex
    title = {"en": "What is your sex?", "ru": "Ваш пол?"}
    await callback.message.edit_text(title.get(lang, title["en"]), reply_markup=sex_keyboard(lang))
    await state.set_state(QState.sex)


# ── Sex ──────────────────────────────────────────────────────
@router.callback_query(F.data.startswith("sex:"), QState.sex)
async def on_sex(callback: CallbackQuery, state: FSMContext):
    sex = callback.data.split(":")[1]
    data = await state.get_data()
    lang = data.get("lang", "ru")
    await callback.answer()
    await state.update_data(sex=sex)

    prompt = {"en": "How old are you? (enter a number)", "ru": "Сколько вам лет? (введите число)"}
    await callback.message.edit_text(prompt.get(lang, prompt["en"]))
    await state.set_state(QState.age)


# ── Age (text input) ─────────────────────────────────────────
@router.message(QState.age)
async def on_age(message: Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get("lang", "ru")
    try:
        age = int(message.text.strip())
        if not 10 <= age <= 120:
            raise ValueError
    except ValueError:
        err = {"en": "Please enter a valid age (10-120):", "ru": "Введите корректный возраст (10-120):"}
        await message.answer(err.get(lang, err["en"]))
        return

    await state.update_data(age=age)
    prompt = {"en": "Your weight in kg? (e.g. 70)", "ru": "Ваш вес в кг? (например 70)"}
    await message.answer(prompt.get(lang, prompt["en"]))
    await state.set_state(QState.weight)


# ── Weight ───────────────────────────────────────────────────
@router.message(QState.weight)
async def on_weight(message: Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get("lang", "ru")
    try:
        weight = float(message.text.strip().replace(",", "."))
        if not 20 <= weight <= 300:
            raise ValueError
    except ValueError:
        err = {"en": "Please enter a valid weight (20-300 kg):", "ru": "Введите корректный вес (20-300 кг):"}
        await message.answer(err.get(lang, err["en"]))
        return

    await state.update_data(weight=weight)
    prompt = {"en": "Your height in cm? (e.g. 170)", "ru": "Ваш рост в см? (например 170)"}
    await message.answer(prompt.get(lang, prompt["en"]))
    await state.set_state(QState.height)


# ── Height ───────────────────────────────────────────────────
@router.message(QState.height)
async def on_height(message: Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get("lang", "ru")
    try:
        height = float(message.text.strip().replace(",", "."))
        if not 100 <= height <= 250:
            raise ValueError
    except ValueError:
        err = {"en": "Please enter valid height (100-250 cm):", "ru": "Введите корректный рост (100-250 см):"}
        await message.answer(err.get(lang, err["en"]))
        return

    await state.update_data(height=height)
    await message.answer(
        _module_title("fitness", lang),
        reply_markup=activity_level_keyboard(lang),
    )
    await state.set_state(QState.activity_level)


# ── Activity Level ───────────────────────────────────────────
@router.callback_query(F.data.startswith("activity:"), QState.activity_level)
async def on_activity(callback: CallbackQuery, state: FSMContext):
    level = callback.data.split(":")[1]
    data = await state.get_data()
    lang = data.get("lang", "ru")
    await callback.answer()
    await state.update_data(activity_level=level)

    await callback.message.edit_text(
        _module_title("diet", lang),
        reply_markup=dietary_pref_keyboard(lang),
    )
    await state.set_state(QState.dietary_pref)


# ── Dietary Preference ───────────────────────────────────────
@router.callback_query(F.data.startswith("diet_pref:"), QState.dietary_pref)
async def on_diet_pref(callback: CallbackQuery, state: FSMContext):
    pref = callback.data.split(":")[1]
    data = await state.get_data()
    lang = data.get("lang", "ru")
    await callback.answer()
    await state.update_data(dietary_pref=pref)

    prompt = {
        "en": "Any food allergies? (type them separated by commas, or type 'none')",
        "ru": "Есть ли пищевые аллергии? (перечислите через запятую или напишите 'нет')",
    }
    await callback.message.edit_text(prompt.get(lang, prompt["en"]))
    await state.set_state(QState.allergies)


# ── Allergies ────────────────────────────────────────────────
@router.message(QState.allergies)
async def on_allergies(message: Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get("lang", "ru")
    text = message.text.strip()
    if text.lower() in ("none", "нет", "-", "no"):
        text = ""
    await state.update_data(allergies=text)

    prompt = {
        "en": "What time do you usually go to bed? (e.g. 23:00)",
        "ru": "Во сколько вы обычно ложитесь спать? (например 23:00)",
    }
    await message.answer(prompt.get(lang, prompt["en"]))
    await state.set_state(QState.sleep_bedtime)


# ── Sleep bedtime ────────────────────────────────────────────
@router.message(QState.sleep_bedtime)
async def on_bedtime(message: Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get("lang", "ru")
    text = message.text.strip()
    # Simple validation
    if ":" not in text:
        text = text + ":00"
    await state.update_data(sleep_bedtime=text[:5])

    prompt = {
        "en": "What time do you usually wake up? (e.g. 07:00)",
        "ru": "Во сколько вы обычно просыпаетесь? (например 07:00)",
    }
    await message.answer(prompt.get(lang, prompt["en"]))
    await state.set_state(QState.sleep_waketime)


# ── Sleep waketime ───────────────────────────────────────────
@router.message(QState.sleep_waketime)
async def on_waketime(message: Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get("lang", "ru")
    text = message.text.strip()
    if ":" not in text:
        text = text + ":00"
    await state.update_data(sleep_waketime=text[:5])

    jobs = {
        "en": [
            ("Sedentary (desk)", "job:sedentary"),
            ("Standing", "job:standing"),
            ("Physical labor", "job:physical"),
        ],
        "ru": [
            ("Сидячая (офис)", "job:sedentary"),
            ("Стоячая", "job:standing"),
            ("Физический труд", "job:physical"),
        ],
    }
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    items = jobs.get(lang, jobs["en"])
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t, callback_data=d)] for t, d in items
    ])
    prompt = {"en": "What type of job do you have?", "ru": "Какой у вас тип работы?"}
    await message.answer(prompt.get(lang, prompt["en"]), reply_markup=kb)
    await state.set_state(QState.job_type)


# ── Job type ─────────────────────────────────────────────────
@router.callback_query(F.data.startswith("job:"), QState.job_type)
async def on_job_type(callback: CallbackQuery, state: FSMContext):
    job = callback.data.split(":")[1]
    data = await state.get_data()
    lang = data.get("lang", "ru")
    await callback.answer()
    await state.update_data(job_type=job)

    stress_opts = {
        "en": [("Low", "stress:low"), ("Medium", "stress:medium"), ("High", "stress:high")],
        "ru": [("Низкий", "stress:low"), ("Средний", "stress:medium"), ("Высокий", "stress:high")],
    }
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    items = stress_opts.get(lang, stress_opts["en"])
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t, callback_data=d) for t, d in items]
    ])
    prompt = {"en": "Your stress level?", "ru": "Ваш уровень стресса?"}
    await callback.message.edit_text(prompt.get(lang, prompt["en"]), reply_markup=kb)
    await state.set_state(QState.stress_level)


# ── Stress level ─────────────────────────────────────────────
@router.callback_query(F.data.startswith("stress:"), QState.stress_level)
async def on_stress(callback: CallbackQuery, state: FSMContext):
    stress = callback.data.split(":")[1]
    data = await state.get_data()
    lang = data.get("lang", "ru")
    await callback.answer()
    await state.update_data(stress_level=stress)

    prompt = {
        "en": "What equipment do you have? (e.g. dumbbells, pull-up bar, none)",
        "ru": "Какое оборудование у вас есть? (например гантели, турник, нет)",
    }
    await callback.message.edit_text(prompt.get(lang, prompt["en"]))
    await state.set_state(QState.equipment)


# ── Equipment ────────────────────────────────────────────────
@router.message(QState.equipment)
async def on_equipment(message: Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get("lang", "ru")
    text = message.text.strip()
    if text.lower() in ("none", "нет", "-", "no"):
        text = ""
    await state.update_data(equipment=text)

    prompt = {
        "en": "How many minutes per week can you exercise? (e.g. 150)",
        "ru": "Сколько минут в неделю вы можете тренироваться? (например 150)",
    }
    await message.answer(prompt.get(lang, prompt["en"]))
    await state.set_state(QState.time_per_week)


# ── Time per week ────────────────────────────────────────────
@router.message(QState.time_per_week)
async def on_time_per_week(message: Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get("lang", "ru")
    try:
        mins = int(message.text.strip())
        if mins < 0:
            raise ValueError
    except ValueError:
        err = {"en": "Please enter a number of minutes:", "ru": "Введите количество минут:"}
        await message.answer(err.get(lang, err["en"]))
        return

    await state.update_data(time_per_week=mins)

    # ── SAVE EVERYTHING ──
    data = await state.get_data()
    await _save_profile(message.from_user.id, data)

    await message.answer(
        t("questionnaire_complete", lang),
        reply_markup=main_keyboard(lang),
    )
    await state.clear()


# ── Helper: save all collected data ──────────────────────────
async def _save_profile(telegram_id: int, data: dict):
    """Calculate BMR/TDEE and save UserProfile."""
    async with async_session() as session:
        result = await session.execute(select(User).where(User.telegram_id == telegram_id))
        user = result.scalar_one_or_none()
        if not user:
            return

        weight = data.get("weight", 70)
        height = data.get("height", 170)
        age = data.get("age", 30)
        sex = data.get("sex", "male")
        activity = data.get("activity_level", "moderate")
        goal = data.get("goal", "health")

        # Mifflin-St Jeor BMR
        if sex == "male":
            bmr = 10 * weight + 6.25 * height - 5 * age + 5
        else:
            bmr = 10 * weight + 6.25 * height - 5 * age - 161

        # Activity multiplier
        multipliers = {
            "sedentary": 1.2,
            "light": 1.375,
            "moderate": 1.55,
            "active": 1.725,
            "very_active": 1.9,
        }
        tdee = bmr * multipliers.get(activity, 1.55)

        # Adjust for goal
        if goal == "weight_loss":
            target_cals = int(tdee - 500)
        elif goal == "muscle":
            target_cals = int(tdee + 300)
        else:
            target_cals = int(tdee)

        # Macros (balanced split)
        target_protein = int(weight * 1.6)  # g
        target_fat = int(target_cals * 0.25 / 9)  # 25% of cals from fat
        target_carbs = int((target_cals - target_protein * 4 - target_fat * 9) / 4)
        target_water = int(weight * 33)  # ml

        # Check if profile exists
        from sqlalchemy import select as sa_select
        existing = await session.execute(
            sa_select(UserProfile).where(UserProfile.user_id == user.id)
        )
        profile = existing.scalar_one_or_none()

        from app.database import UserProfile as UP
        if profile:
            profile.weight_kg = weight
            profile.height_cm = height
            profile.age = age
            profile.sex = sex
            profile.activity_level = activity
            profile.goal = goal
            profile.bmr = round(bmr, 1)
            profile.tdee = round(tdee, 1)
            profile.target_calories = target_cals
            profile.target_protein = target_protein
            profile.target_carbs = target_carbs
            profile.target_fat = target_fat
            profile.target_water_ml = target_water
            profile.parq_passed = data.get("parq_passed", True)
            profile.dietary_pref = data.get("dietary_pref", "none")
            profile.allergies = data.get("allergies", "")
            profile.sleep_bedtime = data.get("sleep_bedtime")
            profile.sleep_waketime = data.get("sleep_waketime")
            profile.job_type = data.get("job_type")
            profile.stress_level = data.get("stress_level")
            profile.equipment = data.get("equipment", "")
            profile.time_per_week_mins = data.get("time_per_week", 150)
        else:
            profile = UserProfile(
                user_id=user.id,
                weight_kg=weight,
                height_cm=height,
                age=age,
                sex=sex,
                activity_level=activity,
                goal=goal,
                bmr=round(bmr, 1),
                tdee=round(tdee, 1),
                target_calories=target_cals,
                target_protein=target_protein,
                target_carbs=target_carbs,
                target_fat=target_fat,
                target_water_ml=target_water,
                parq_passed=data.get("parq_passed", True),
                dietary_pref=data.get("dietary_pref", "none"),
                allergies=data.get("allergies", ""),
                sleep_bedtime=data.get("sleep_bedtime"),
                sleep_waketime=data.get("sleep_waketime"),
                job_type=data.get("job_type"),
                stress_level=data.get("stress_level"),
                equipment=data.get("equipment", ""),
                time_per_week_mins=data.get("time_per_week", 150),
            )
            session.add(profile)

        # Create streak record
        from app.database import UserStreak as US
        streak_exists = await session.execute(
            sa_select(US).where(US.user_id == user.id)
        )
        if not streak_exists.scalar_one_or_none():
            session.add(US(user_id=user.id))

        # Create reminder settings
        from app.database import ReminderSettings as RS
        reminder_exists = await session.execute(
            sa_select(RS).where(RS.user_id == user.id)
        )
        if not reminder_exists.scalar_one_or_none():
            session.add(RS(user_id=user.id))

        user.onboarding_complete = True
        await session.commit()

    logger.info(f"Profile saved for user {telegram_id}: BMR={bmr:.0f}, TDEE={tdee:.0f}, target={target_cals} kcal")


def _module_title(module: str, lang: str) -> str:
    titles = {
        "parq": {"en": "Physical Activity Readiness Questionnaire", "ru": "Анкета готовности к физической активности"},
        "goals": {"en": "What's your primary goal?", "ru": "Какова ваша главная цель?"},
        "fitness": {"en": "Your fitness level:", "ru": "Ваш уровень активности:"},
        "diet": {"en": "Dietary preferences:", "ru": "Предпочтения в питании:"},
        "sleep": {"en": "Sleep schedule:", "ru": "Режим сна:"},
        "lifestyle": {"en": "Your lifestyle:", "ru": "Ваш образ жизни:"},
    }
    entry = titles.get(module, {})
    return entry.get(lang, entry.get("en", module))
