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
            "Я ваш бесплатный персональный помощник по здоровью и фитнесу.\n"
            "Давайте вместе создадим план, который подойдёт именно вам.\n\n"
            "Нажмите кнопку ниже, чтобы начать — это займёт всего пару минут."
        ),
    },
    "choose_language": {
        "en": "Please choose your language:",
        "ru": "Пожалуйста, выберите удобный язык:",
    },
    "language_set": {
        "en": "Language set to English",
        "ru": "Отлично! Язык установлен — Русский",
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
            "Прежде чем мы начнём, хотим вас предупредить:\n\n"
            "Это приложение помогает с общими рекомендациями по фитнесу и питанию. "
            "Это НЕ замена медицинской консультации. Пожалуйста, обязательно "
            "посоветуйтесь с вашим врачом перед началом любых упражнений или диеты.\n\n"
            "Вы согласны продолжить?"
        ),
    },
    "consent_declined": {
        "en": "You need to accept the disclaimer to use VitaFit. Type /start to try again.",
        "ru": "Для использования VitaFit нужно принять условия. Просто введите /start, чтобы начать заново.",
    },
    "privacy_notice": {
        "en": "Your health data stays private and is never shared or sold.",
        "ru": "Ваши данные о здоровье конфиденциальны и никогда не передаются третьим лицам.",
    },
    "questionnaire_complete": {
        "en": (
            "Questionnaire complete!\n\n"
            "Your personalized plan is ready.\n"
            "Open the mini-app to see your exercise and meal plans."
        ),
        "ru": (
            "Отлично! Ваш персональный план готов!\n\n"
            "Мы подобрали для вас упражнения и рекомендации по питанию.\n"
            "Откройте приложение, чтобы всё посмотреть — вам понравится!"
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
            "Судя по вашим ответам, будет лучше сначала проконсультироваться "
            "с врачом перед началом тренировок.\n\n"
            "Не переживайте — мы подберём для вас мягкие и безопасные упражнения: "
            "лёгкие прогулки, растяжку и тай-чи. Это будет приятно и полезно!"
        ),
    },
    "reminder_morning": {
        "en": "Good morning! Here's your plan for today:\n\n",
        "ru": "Доброе утро! Надеемся, вы хорошо отдохнули. Вот ваш план на сегодня:\n\n",
    },
    "reminder_evening": {
        "en": "Time to check in! How did today go?\n\n",
        "ru": "Добрый вечер! Как прошёл ваш день? Давайте подведём итоги:\n\n",
    },
    "streak_congrats": {
        "en": "You're on a {{streak}}-day streak! Keep it up!",
        "ru": "Замечательно! Уже {{streak}} дней подряд — вы молодец! Так держать!",
    },
    "streak_lost": {
        "en": "Don't worry about yesterday — every day is a fresh start! Let's get back on track.",
        "ru": "Ничего страшного, что вчера не получилось — такое бывает у всех! Каждый новый день это новая возможность. Давайте продолжим вместе!",
    },
    "weekly_summary": {
        "en": "Your weekly summary is ready! Check your progress in the mini-app.",
        "ru": "Ваш недельный отчёт готов! Посмотрите, сколько вы уже достигли — мы вами гордимся!",
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
        "ru": "Согласна",
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
            "VitaFit — Ваш бесплатный помощник по здоровью\n\n"
            "Вот что я умею:\n"
            "/start — Запустить бота\n"
            "/plan — Посмотреть ваш план\n"
            "/log — Записать приём пищи\n"
            "/water — Записать выпитую воду\n"
            "/streak — Посмотреть вашу серию\n"
            "/settings — Настройки (язык, напоминания)\n"
            "/help — Показать эту подсказку"
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
