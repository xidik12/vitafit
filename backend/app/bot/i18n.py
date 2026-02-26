"""Bot-side i18n — simple dict-based translations."""

_TRANSLATIONS = {
    "welcome": {
        "en": (
            "Welcome to VitaFit!\n\n"
            "I'm your free personal health & fitness coach.\n"
            "Let's create a plan tailored just for you.\n\n"
            "Tap the button below to start the questionnaire."
        ),
        "ru": (
            "Добро пожаловать в VitaFit!\n\n"
            "Я ваш бесплатный персональный тренер по здоровью.\n"
            "Давайте создадим план, подходящий именно вам.\n\n"
            "Нажмите кнопку ниже, чтобы начать анкету."
        ),
    },
    "choose_language": {
        "en": "Please choose your language:",
        "ru": "Пожалуйста, выберите язык:",
    },
    "language_set": {
        "en": "Language set to English",
        "ru": "Язык изменён на Русский",
    },
    "consent_prompt": {
        "en": (
            "Before we begin, please note:\n\n"
            "This app provides general fitness and nutrition guidance. "
            "It is NOT medical advice. Always consult a doctor before starting "
            "any exercise or diet program.\n\n"
            "Do you agree to continue?"
        ),
        "ru": (
            "Прежде чем начать, обратите внимание:\n\n"
            "Это приложение даёт общие рекомендации по фитнесу и питанию. "
            "Это НЕ медицинский совет. Всегда консультируйтесь с врачом "
            "перед началом любой программы упражнений или диеты.\n\n"
            "Вы согласны продолжить?"
        ),
    },
    "consent_declined": {
        "en": "You need to accept the disclaimer to use VitaFit. Type /start to try again.",
        "ru": "Для использования VitaFit необходимо принять условия. Введите /start, чтобы попробовать снова.",
    },
    "questionnaire_complete": {
        "en": (
            "Questionnaire complete!\n\n"
            "Your personalized plan is ready.\n"
            "Open the mini-app to see your exercise and meal plans."
        ),
        "ru": (
            "Анкета заполнена!\n\n"
            "Ваш персональный план готов.\n"
            "Откройте мини-приложение, чтобы увидеть планы тренировок и питания."
        ),
    },
    "parq_warning": {
        "en": (
            "Based on your answers, we recommend consulting a doctor "
            "before starting an exercise program.\n\n"
            "Your plan will be adjusted to include only gentle activities "
            "like walking, stretching, and tai chi."
        ),
        "ru": (
            "По результатам анкеты мы рекомендуем проконсультироваться "
            "с врачом перед началом тренировок.\n\n"
            "Ваш план будет скорректирован и будет включать только лёгкие "
            "упражнения: ходьба, растяжка и тай-чи."
        ),
    },
    "reminder_morning": {
        "en": "Good morning! Here's your plan for today:\n\n",
        "ru": "Доброе утро! Вот ваш план на сегодня:\n\n",
    },
    "reminder_evening": {
        "en": "Time to check in! How did today go?\n\n",
        "ru": "Время подвести итоги! Как прошёл день?\n\n",
    },
    "streak_congrats": {
        "en": "You're on a {{streak}}-day streak! Keep it up!",
        "ru": "Ваша серия — {{streak}} дней! Так держать!",
    },
    "streak_lost": {
        "en": "Don't worry about yesterday — every day is a fresh start! Let's get back on track.",
        "ru": "Не переживайте о вчерашнем дне — каждый день это новый старт! Давайте вернёмся в строй.",
    },
    "weekly_summary": {
        "en": "Your weekly summary is ready! Check your progress in the mini-app.",
        "ru": "Ваш недельный отчёт готов! Посмотрите прогресс в мини-приложении.",
    },
    "btn_start_questionnaire": {
        "en": "Start Questionnaire",
        "ru": "Начать анкету",
    },
    "btn_open_app": {
        "en": "Open VitaFit",
        "ru": "Открыть VitaFit",
    },
    "btn_yes": {
        "en": "Yes",
        "ru": "Да",
    },
    "btn_no": {
        "en": "No",
        "ru": "Нет",
    },
    "btn_agree": {
        "en": "I Agree",
        "ru": "Согласен(а)",
    },
    "btn_decline": {
        "en": "Decline",
        "ru": "Отказаться",
    },
    "help": {
        "en": (
            "VitaFit — Your Free Health Coach\n\n"
            "Commands:\n"
            "/start — Start the bot\n"
            "/plan — View your plan\n"
            "/log — Quick food log\n"
            "/water — Log water\n"
            "/streak — Check your streak\n"
            "/settings — Change language, reminders\n"
            "/help — Show this message"
        ),
        "ru": (
            "VitaFit — Ваш бесплатный тренер по здоровью\n\n"
            "Команды:\n"
            "/start — Запустить бота\n"
            "/plan — Посмотреть план\n"
            "/log — Быстрая запись еды\n"
            "/water — Записать воду\n"
            "/streak — Проверить серию\n"
            "/settings — Изменить язык, напоминания\n"
            "/help — Показать эту справку"
        ),
    },
}


def t(key: str, lang: str = "ru", **kwargs) -> str:
    """Get translated string by key and language."""
    entry = _TRANSLATIONS.get(key, {})
    text = entry.get(lang, entry.get("en", f"[{key}]"))
    for k, v in kwargs.items():
        text = text.replace("{{" + k + "}}", str(v))
    return text
