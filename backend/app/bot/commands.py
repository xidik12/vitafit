import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from sqlalchemy import select

from app.database import async_session, User, UserStreak
from app.bot.i18n import t
from app.bot.keyboards import language_keyboard, main_keyboard

logger = logging.getLogger(__name__)
router = Router()


async def get_or_create_user(telegram_id: int, username: str | None = None, first_name: str | None = None) -> User:
    async with async_session() as session:
        result = await session.execute(select(User).where(User.telegram_id == telegram_id))
        user = result.scalar_one_or_none()
        if not user:
            user = User(
                telegram_id=telegram_id,
                username=username,
                first_name=first_name,
                language="ru",
            )
            session.add(user)
            await session.commit()
            await session.refresh(user)
        return user


@router.message(Command("start"))
async def cmd_start(message: Message):
    user = await get_or_create_user(
        message.from_user.id,
        message.from_user.username,
        message.from_user.first_name,
    )
    await message.answer(
        t("choose_language", user.language),
        reply_markup=language_keyboard(),
    )


@router.callback_query(F.data.startswith("lang:"))
async def on_language(callback: CallbackQuery):
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

    await callback.message.edit_text(t("language_set", lang))
    await callback.message.answer(
        t("welcome", lang),
        reply_markup=main_keyboard(lang),
    )


@router.message(Command("help"))
async def cmd_help(message: Message):
    user = await get_or_create_user(message.from_user.id)
    await message.answer(t("help", user.language), parse_mode="HTML")


@router.message(Command("plan"))
async def cmd_plan(message: Message):
    user = await get_or_create_user(message.from_user.id)
    await message.answer(
        t("btn_open_app", user.language),
        reply_markup=main_keyboard(user.language),
    )


@router.message(Command("streak"))
async def cmd_streak(message: Message):
    user = await get_or_create_user(message.from_user.id)
    async with async_session() as session:
        result = await session.execute(select(UserStreak).where(UserStreak.user_id == user.id))
        streak = result.scalar_one_or_none()
    if not streak:
        text = t("streak_congrats", user.language, streak=0)
    else:
        text = t("streak_congrats", user.language, streak=streak.current_streak)
    await message.answer(text)


@router.message(Command("water"))
async def cmd_water(message: Message):
    from datetime import date as dt_date
    from app.database import WaterLog
    user = await get_or_create_user(message.from_user.id)
    parts = message.text.split()
    amount = 250
    if len(parts) > 1:
        try:
            amount = int(parts[1])
        except ValueError:
            pass
    async with async_session() as session:
        log = WaterLog(user_id=user.id, date=dt_date.today(), amount_ml=amount)
        session.add(log)
        await session.commit()
    if user.language == "ru":
        await message.answer(f"Записано {amount} мл воды")
    else:
        await message.answer(f"Logged {amount} ml of water")


@router.message(Command("settings"))
async def cmd_settings(message: Message):
    user = await get_or_create_user(message.from_user.id)
    await message.answer(
        t("choose_language", user.language),
        reply_markup=language_keyboard(),
    )
