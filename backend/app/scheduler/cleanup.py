"""Cleanup jobs — old data removal."""
import logging
from datetime import datetime, timedelta
from sqlalchemy import delete

from app.database import async_session, CalorieLog, WaterLog

logger = logging.getLogger(__name__)


async def cleanup_old_logs():
    """Remove logs older than 1 year."""
    cutoff = datetime.utcnow() - timedelta(days=365)
    async with async_session() as session:
        # We don't delete weight logs (valuable for long-term trends)
        # Only clean very old calorie/water logs
        await session.execute(
            delete(CalorieLog).where(CalorieLog.created_at < cutoff)
        )
        await session.execute(
            delete(WaterLog).where(WaterLog.created_at < cutoff)
        )
        await session.commit()
    logger.info("Old logs cleaned up")
