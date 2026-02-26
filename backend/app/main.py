import asyncio
import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.config import settings
from app.database import init_db
from app.api import auth, profile, questionnaire, exercises, recipes, calories, tasks, progress, admin

logging.basicConfig(
    level=logging.DEBUG if settings.debug else logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler(timezone="utc")

_bot = None
_bot_task = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _bot, _bot_task
    logger.info("VitaFit starting up...")

    # Initialize database
    await init_db()
    logger.info("Database initialized")

    # Seed Russian foods
    try:
        from app.scheduler.jobs import seed_russian_foods
        await seed_russian_foods()
    except Exception as e:
        logger.error(f"Seed Russian foods failed: {e}")

    # Load exercises from Free Exercise DB
    try:
        from app.collectors.exercise_db import load_exercises
        asyncio.create_task(load_exercises())
    except Exception as e:
        logger.error(f"Exercise DB load failed: {e}")

    # Scheduler jobs
    _job_defaults = dict(max_instances=1, coalesce=True, misfire_grace_time=300)

    # Reminders
    try:
        from app.scheduler.reminders import send_morning_reminders, send_evening_reminders
        scheduler.add_job(send_morning_reminders, "interval", hours=1, id="morning_reminders", **_job_defaults)
        scheduler.add_job(send_evening_reminders, "interval", hours=1, id="evening_reminders", **_job_defaults)
    except Exception as e:
        logger.warning(f"Reminder jobs not registered: {e}")

    # Weekly summary (Sunday at 10:00 UTC)
    try:
        from app.scheduler.weekly_summary import send_weekly_summaries
        scheduler.add_job(send_weekly_summaries, "cron", day_of_week="sun", hour=10, id="weekly_summary", **_job_defaults)
    except Exception as e:
        logger.warning(f"Weekly summary job not registered: {e}")

    # Weekly skip reset (Monday at 00:00 UTC)
    try:
        from app.services.accountability import reset_weekly_skip
        scheduler.add_job(reset_weekly_skip, "cron", day_of_week="mon", hour=0, id="reset_weekly_skip", **_job_defaults)
    except Exception as e:
        logger.warning(f"Weekly skip reset job not registered: {e}")

    # Data sync (daily at 03:00 UTC)
    try:
        from app.scheduler.data_sync import sync_exercise_db, sync_recipes
        scheduler.add_job(sync_exercise_db, "cron", hour=3, minute=0, id="sync_exercises", **_job_defaults)
        scheduler.add_job(sync_recipes, "cron", hour=3, minute=30, id="sync_recipes", **_job_defaults)
    except Exception as e:
        logger.warning(f"Data sync jobs not registered: {e}")

    # Cleanup (daily at 04:00 UTC)
    try:
        from app.scheduler.cleanup import cleanup_old_logs
        scheduler.add_job(cleanup_old_logs, "cron", hour=4, minute=0, id="cleanup", **_job_defaults)
    except Exception as e:
        logger.warning(f"Cleanup job not registered: {e}")

    scheduler.start()
    logger.info("Scheduler started")

    # Start Telegram bot
    if settings.telegram_bot_token:
        try:
            from app.bot.bot import create_bot
            bot, dp = create_bot()
            _bot = bot

            # Set bot reference in reminder/summary modules
            try:
                from app.scheduler.reminders import set_bot
                set_bot(bot)
            except Exception:
                pass
            try:
                from app.scheduler.weekly_summary import set_bot as set_summary_bot
                set_summary_bot(bot)
            except Exception:
                pass

            # Set bot commands
            try:
                from aiogram.types import BotCommand
                await bot.set_my_commands([
                    BotCommand(command="start", description="Start the bot"),
                    BotCommand(command="help", description="Show help"),
                    BotCommand(command="plan", description="View your plan"),
                    BotCommand(command="streak", description="Check your streak"),
                    BotCommand(command="water", description="Log water (e.g. /water 250)"),
                    BotCommand(command="settings", description="Change language"),
                ])
                await bot.set_my_description(
                    "VitaFit — Your free personal health & fitness coach.\n\n"
                    "Personalized exercise plans (incl. tai chi & yoga), "
                    "halal meal plans, calorie tracking, and accountability."
                )
                await bot.set_my_short_description(
                    "Free health & fitness coach with personalized plans."
                )
            except Exception as e:
                logger.warning(f"Bot commands/description failed: {e}")

            # Clear stale webhooks
            try:
                await bot.delete_webhook(drop_pending_updates=True)
            except Exception:
                pass

            await asyncio.sleep(2)

            async def _run_bot_polling():
                retry_delay = 5
                while True:
                    try:
                        logger.info("Bot polling starting...")
                        await dp.start_polling(bot)
                        break
                    except Exception as e:
                        err_str = str(e).lower()
                        if "conflict" in err_str or "409" in err_str:
                            logger.warning("Bot polling: 409 conflict, stopping")
                            break
                        logger.error(f"Bot polling crashed: {e}, retrying in {retry_delay}s")
                        await asyncio.sleep(retry_delay)
                        retry_delay = min(retry_delay * 2, 60)

            _bot_task = asyncio.create_task(_run_bot_polling())
            logger.info("Telegram bot started")
        except Exception as e:
            logger.error(f"Failed to start bot: {e}")
    else:
        logger.warning("TELEGRAM_BOT_TOKEN not set — bot disabled")

    logger.info("VitaFit startup complete")

    yield

    # Shutdown
    try:
        scheduler.shutdown()
    except Exception:
        pass

    if _bot_task:
        _bot_task.cancel()
    if _bot:
        await _bot.session.close()

    from app.redis_client import close_redis
    await close_redis()

    logger.info("VitaFit shut down")


app = FastAPI(
    title="VitaFit",
    description="Free personal health & fitness coach",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS
_cors_origins = [
    "https://web.telegram.org",
    "https://webk.telegram.org",
    "https://webz.telegram.org",
]
if settings.debug:
    _cors_origins.extend(["http://localhost:5173", "http://localhost:3000"])
if settings.telegram_webapp_url:
    _cors_origins.append(settings.telegram_webapp_url.rstrip("/"))

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers (routers already have their own prefixes)
app.include_router(auth.router)
app.include_router(profile.router)
app.include_router(questionnaire.router)
app.include_router(exercises.router)
app.include_router(recipes.router)
app.include_router(calories.router)
app.include_router(tasks.router)
app.include_router(progress.router)
app.include_router(admin.router)


@app.get("/health")
async def health():
    return {"status": "ok"}


# Serve Mini App frontend (production build)
_local_dist = Path(__file__).parent.parent.parent / "webapp" / "dist"
_docker_dist = Path("/webapp/dist")
WEBAPP_DIST = _local_dist if _local_dist.exists() else _docker_dist


@app.get("/")
async def serve_root():
    if WEBAPP_DIST.exists():
        return FileResponse(
            WEBAPP_DIST / "index.html",
            headers={"Cache-Control": "no-cache, no-store, must-revalidate"},
        )
    return {"name": "VitaFit", "version": "1.0.0", "status": "running"}


if WEBAPP_DIST.exists():
    app.mount("/assets", StaticFiles(directory=WEBAPP_DIST / "assets"), name="static")

    @app.exception_handler(StarletteHTTPException)
    async def spa_404_handler(request: Request, exc: StarletteHTTPException):
        if exc.status_code == 404 and not request.url.path.startswith("/api"):
            static_file = (WEBAPP_DIST / request.url.path.lstrip("/")).resolve()
            if (
                static_file.exists()
                and static_file.is_file()
                and str(static_file).startswith(str(WEBAPP_DIST.resolve()))
            ):
                return FileResponse(static_file)
            return FileResponse(
                WEBAPP_DIST / "index.html",
                headers={"Cache-Control": "no-cache, no-store, must-revalidate"},
            )
        raise exc
