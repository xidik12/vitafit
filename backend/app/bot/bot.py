import logging
import time
from aiogram import Bot, Dispatcher, BaseMiddleware
from app.config import settings
from app.bot.commands import router as commands_router

logger = logging.getLogger(__name__)


class ThrottleMiddleware(BaseMiddleware):
    _timestamps: dict[int, float] = {}
    RATE_LIMIT = 1.0

    async def __call__(self, handler, event, data):
        user_id = getattr(getattr(event, 'from_user', None), 'id', None)
        if user_id:
            now = time.time()
            last = self._timestamps.get(user_id, 0)
            if now - last < self.RATE_LIMIT:
                return
            self._timestamps[user_id] = now
        return await handler(event, data)


def create_bot() -> tuple[Bot, Dispatcher]:
    bot = Bot(token=settings.telegram_bot_token)
    dp = Dispatcher()
    commands_router.message.middleware(ThrottleMiddleware())
    commands_router.callback_query.middleware(ThrottleMiddleware())
    dp.include_router(commands_router)
    return bot, dp
