"""Telegram inline keyboards for VitaFit bot."""
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from app.config import settings


def language_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Русский", callback_data="lang:ru"),
            InlineKeyboardButton(text="English", callback_data="lang:en"),
        ]
    ])


def consent_keyboard(lang: str = "ru") -> InlineKeyboardMarkup:
    from app.bot.i18n import t
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=t("btn_agree", lang), callback_data="consent:yes"),
            InlineKeyboardButton(text=t("btn_decline", lang), callback_data="consent:no"),
        ]
    ])


def main_keyboard(lang: str = "ru") -> InlineKeyboardMarkup:
    from app.bot.i18n import t
    buttons = []
    webapp_url = settings.effective_webapp_url
    if webapp_url:
        buttons.append([InlineKeyboardButton(
            text=t("btn_open_app", lang),
            web_app=WebAppInfo(url=webapp_url),
        )])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def yes_no_keyboard(lang: str = "ru") -> InlineKeyboardMarkup:
    from app.bot.i18n import t
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=t("btn_yes", lang), callback_data="answer:yes"),
            InlineKeyboardButton(text=t("btn_no", lang), callback_data="answer:no"),
        ]
    ])


def questionnaire_goals_keyboard(lang: str = "ru") -> InlineKeyboardMarkup:
    goals = {
        "en": [
            ("Lose Weight", "goal:weight_loss"),
            ("Build Muscle", "goal:muscle"),
            ("Improve Flexibility", "goal:flexibility"),
            ("General Health", "goal:health"),
            ("Stress Relief", "goal:stress_relief"),
        ],
        "ru": [
            ("Похудеть", "goal:weight_loss"),
            ("Набрать мышцы", "goal:muscle"),
            ("Гибкость", "goal:flexibility"),
            ("Общее здоровье", "goal:health"),
            ("Снятие стресса", "goal:stress_relief"),
        ],
    }
    items = goals.get(lang, goals["en"])
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=text, callback_data=data)] for text, data in items
    ])


def activity_level_keyboard(lang: str = "ru") -> InlineKeyboardMarkup:
    levels = {
        "en": [
            ("Sedentary (desk job)", "activity:sedentary"),
            ("Light (1-2x/week)", "activity:light"),
            ("Moderate (3-5x/week)", "activity:moderate"),
            ("Active (6-7x/week)", "activity:active"),
            ("Very Active (athlete)", "activity:very_active"),
        ],
        "ru": [
            ("Сидячий (офис)", "activity:sedentary"),
            ("Лёгкий (1-2 р/нед)", "activity:light"),
            ("Умеренный (3-5 р/нед)", "activity:moderate"),
            ("Активный (6-7 р/нед)", "activity:active"),
            ("Очень активный (спортсмен)", "activity:very_active"),
        ],
    }
    items = levels.get(lang, levels["en"])
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=text, callback_data=data)] for text, data in items
    ])


def dietary_pref_keyboard(lang: str = "ru") -> InlineKeyboardMarkup:
    prefs = {
        "en": [
            ("Halal", "diet_pref:halal"),
            ("Vegetarian", "diet_pref:vegetarian"),
            ("Vegan", "diet_pref:vegan"),
            ("No Restrictions", "diet_pref:none"),
        ],
        "ru": [
            ("Халяль", "diet_pref:halal"),
            ("Вегетарианское", "diet_pref:vegetarian"),
            ("Веганское", "diet_pref:vegan"),
            ("Без ограничений", "diet_pref:none"),
        ],
    }
    items = prefs.get(lang, prefs["en"])
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=text, callback_data=data)] for text, data in items
    ])


def sex_keyboard(lang: str = "ru") -> InlineKeyboardMarkup:
    items = {
        "en": [("Male", "sex:male"), ("Female", "sex:female")],
        "ru": [("Мужской", "sex:male"), ("Женский", "sex:female")],
    }
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t, callback_data=d) for t, d in items.get(lang, items["en"])]
    ])
