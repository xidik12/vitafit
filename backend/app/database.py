import logging
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import Text, Float, Integer, BigInteger, String, JSON, DateTime, Boolean, Date, ForeignKey, func
from datetime import datetime, date

from app.config import settings

_db_logger = logging.getLogger(__name__)


def _create_engine():
    url = settings.async_database_url
    if settings.is_postgres:
        _db_logger.info("Using PostgreSQL backend")
        return create_async_engine(
            url, echo=False, pool_size=10, max_overflow=20,
            pool_pre_ping=True, pool_recycle=1800, pool_timeout=10,
            connect_args={"command_timeout": 30},
        )
    _db_logger.info("Using SQLite backend")
    return create_async_engine(url, echo=False)


engine = _create_engine()
async_session = async_sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
    username: Mapped[str | None] = mapped_column(String(255), nullable=True)
    first_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    language: Mapped[str] = mapped_column(String(5), default="ru")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    onboarding_complete: Mapped[bool] = mapped_column(Boolean, default=False)
    consent_given: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())


class UserProfile(Base):
    __tablename__ = "user_profiles"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), unique=True, index=True)
    weight_kg: Mapped[float | None] = mapped_column(Float, nullable=True)
    height_cm: Mapped[float | None] = mapped_column(Float, nullable=True)
    age: Mapped[int | None] = mapped_column(Integer, nullable=True)
    sex: Mapped[str | None] = mapped_column(String(10), nullable=True)  # male/female
    activity_level: Mapped[str | None] = mapped_column(String(20), nullable=True)  # sedentary/light/moderate/active/very_active
    goal: Mapped[str | None] = mapped_column(String(30), nullable=True)  # weight_loss/muscle/flexibility/health/stress_relief
    bmr: Mapped[float | None] = mapped_column(Float, nullable=True)
    tdee: Mapped[float | None] = mapped_column(Float, nullable=True)
    target_calories: Mapped[int | None] = mapped_column(Integer, nullable=True)
    target_protein: Mapped[int | None] = mapped_column(Integer, nullable=True)
    target_carbs: Mapped[int | None] = mapped_column(Integer, nullable=True)
    target_fat: Mapped[int | None] = mapped_column(Integer, nullable=True)
    target_water_ml: Mapped[int | None] = mapped_column(Integer, nullable=True)
    parq_passed: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    dietary_pref: Mapped[str | None] = mapped_column(String(20), nullable=True)  # halal/vegetarian/vegan/none
    allergies: Mapped[str | None] = mapped_column(Text, nullable=True)  # comma-separated
    sleep_bedtime: Mapped[str | None] = mapped_column(String(5), nullable=True)  # HH:MM
    sleep_waketime: Mapped[str | None] = mapped_column(String(5), nullable=True)
    job_type: Mapped[str | None] = mapped_column(String(20), nullable=True)  # sedentary/standing/physical
    stress_level: Mapped[str | None] = mapped_column(String(10), nullable=True)  # low/medium/high
    equipment: Mapped[str | None] = mapped_column(Text, nullable=True)  # comma-separated
    time_per_week_mins: Mapped[int | None] = mapped_column(Integer, nullable=True)


class Exercise(Base):
    __tablename__ = "exercises"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name_en: Mapped[str] = mapped_column(String(255))
    name_ru: Mapped[str | None] = mapped_column(String(255), nullable=True)
    body_part: Mapped[str | None] = mapped_column(String(50), nullable=True)
    target_muscle: Mapped[str | None] = mapped_column(String(50), nullable=True)
    equipment: Mapped[str | None] = mapped_column(String(50), nullable=True)
    difficulty: Mapped[str | None] = mapped_column(String(20), nullable=True)  # beginner/intermediate/advanced
    instructions: Mapped[str | None] = mapped_column(Text, nullable=True)
    instructions_ru: Mapped[str | None] = mapped_column(Text, nullable=True)
    images: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    source: Mapped[str | None] = mapped_column(String(50), nullable=True)
    exercise_type: Mapped[str | None] = mapped_column(String(20), nullable=True)  # strength/cardio/flexibility/tai_chi/yoga


class ExercisePlan(Base):
    __tablename__ = "exercise_plans"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), index=True)
    week_number: Mapped[int] = mapped_column(Integer)
    plan_json: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())


class DailyTask(Base):
    __tablename__ = "daily_tasks"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), index=True)
    date: Mapped[date] = mapped_column(Date, index=True)
    task_type: Mapped[str] = mapped_column(String(20))  # exercise/meal/water
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_completed: Mapped[bool] = mapped_column(Boolean, default=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class Recipe(Base):
    __tablename__ = "recipes"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title_en: Mapped[str] = mapped_column(String(500))
    title_ru: Mapped[str | None] = mapped_column(String(500), nullable=True)
    source_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    image_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    instructions: Mapped[str | None] = mapped_column(Text, nullable=True)
    instructions_ru: Mapped[str | None] = mapped_column(Text, nullable=True)
    cook_time_mins: Mapped[int | None] = mapped_column(Integer, nullable=True)
    servings: Mapped[int | None] = mapped_column(Integer, nullable=True)
    calories_per_serving: Mapped[float | None] = mapped_column(Float, nullable=True)
    protein: Mapped[float | None] = mapped_column(Float, nullable=True)
    carbs: Mapped[float | None] = mapped_column(Float, nullable=True)
    fat: Mapped[float | None] = mapped_column(Float, nullable=True)
    diet_type: Mapped[str | None] = mapped_column(String(20), nullable=True)  # halal/vegetarian/vegan
    cuisine: Mapped[str | None] = mapped_column(String(50), nullable=True)
    source_api: Mapped[str | None] = mapped_column(String(30), nullable=True)
    spoonacular_id: Mapped[int | None] = mapped_column(Integer, nullable=True)


class RecipeIngredient(Base):
    __tablename__ = "recipe_ingredients"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    recipe_id: Mapped[int] = mapped_column(Integer, ForeignKey("recipes.id"), index=True)
    name: Mapped[str] = mapped_column(String(255))
    amount: Mapped[float | None] = mapped_column(Float, nullable=True)
    unit: Mapped[str | None] = mapped_column(String(30), nullable=True)


class MealPlan(Base):
    __tablename__ = "meal_plans"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), index=True)
    week_number: Mapped[int] = mapped_column(Integer)
    plan_json: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())


class FoodItem(Base):
    __tablename__ = "food_items"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name_en: Mapped[str] = mapped_column(String(500))
    name_ru: Mapped[str | None] = mapped_column(String(500), nullable=True)
    barcode: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)
    source: Mapped[str | None] = mapped_column(String(30), nullable=True)  # usda/openfoodfacts/custom
    calories_per_100g: Mapped[float | None] = mapped_column(Float, nullable=True)
    protein_per_100g: Mapped[float | None] = mapped_column(Float, nullable=True)
    carbs_per_100g: Mapped[float | None] = mapped_column(Float, nullable=True)
    fat_per_100g: Mapped[float | None] = mapped_column(Float, nullable=True)
    fiber_per_100g: Mapped[float | None] = mapped_column(Float, nullable=True)
    serving_size_g: Mapped[float | None] = mapped_column(Float, nullable=True)


class CalorieLog(Base):
    __tablename__ = "calorie_logs"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), index=True)
    date: Mapped[date] = mapped_column(Date, index=True)
    meal_type: Mapped[str] = mapped_column(String(20))  # breakfast/lunch/dinner/snack
    food_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("food_items.id"), nullable=True)
    food_name_override: Mapped[str | None] = mapped_column(String(500), nullable=True)
    amount_g: Mapped[float] = mapped_column(Float)
    calories: Mapped[float] = mapped_column(Float)
    protein: Mapped[float | None] = mapped_column(Float, nullable=True)
    carbs: Mapped[float | None] = mapped_column(Float, nullable=True)
    fat: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())


class WaterLog(Base):
    __tablename__ = "water_logs"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), index=True)
    date: Mapped[date] = mapped_column(Date)
    amount_ml: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())


class WeightLog(Base):
    __tablename__ = "weight_logs"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), index=True)
    date: Mapped[date] = mapped_column(Date)
    weight_kg: Mapped[float] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())


class UserStreak(Base):
    __tablename__ = "user_streaks"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), unique=True, index=True)
    current_streak: Mapped[int] = mapped_column(Integer, default=0)
    longest_streak: Mapped[int] = mapped_column(Integer, default=0)
    xp_total: Mapped[int] = mapped_column(Integer, default=0)
    level: Mapped[int] = mapped_column(Integer, default=1)
    skip_used_this_week: Mapped[bool] = mapped_column(Boolean, default=False)
    last_active_date: Mapped[date | None] = mapped_column(Date, nullable=True)


class Achievement(Base):
    __tablename__ = "achievements"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), index=True)
    achievement_type: Mapped[str] = mapped_column(String(50))
    earned_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())


class ReminderSettings(Base):
    __tablename__ = "reminder_settings"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), unique=True, index=True)
    morning_time: Mapped[str] = mapped_column(String(5), default="08:00")
    evening_time: Mapped[str] = mapped_column(String(5), default="21:00")
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    timezone: Mapped[str] = mapped_column(String(50), default="Asia/Tashkent")


class QuestionnaireAnswer(Base):
    __tablename__ = "questionnaire_answers"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), index=True)
    module: Mapped[str] = mapped_column(String(30))  # parq/goals/fitness/diet/sleep/lifestyle
    question_key: Mapped[str] = mapped_column(String(100))
    answer_value: Mapped[str | None] = mapped_column(Text, nullable=True)


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    _db_logger.info("Database tables created/verified")
