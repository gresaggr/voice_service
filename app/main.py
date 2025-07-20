import asyncio
import logging
from contextlib import asynccontextmanager

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram_dialog import setup_dialogs
from loguru import logger

from app.config import settings
from app.database.engine import db_manager
from app.bot.handlers import setup_handlers
from app.bot.middlewares.auth import AuthMiddleware
from app.bot.middlewares.throttling import ThrottlingMiddleware


async def setup_bot() -> tuple[Bot, Dispatcher]:
    """Setup bot and dispatcher with all components."""
    
    # Initialize bot
    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(
            parse_mode=ParseMode.HTML
        )
    )
    
    # Initialize dispatcher
    dp = Dispatcher()
    
    # Setup middlewares
    dp.message.middleware(ThrottlingMiddleware())
    dp.callback_query.middleware(ThrottlingMiddleware())
    dp.message.middleware(AuthMiddleware())
    dp.callback_query.middleware(AuthMiddleware())
    
    # Setup handlers
    setup_handlers(dp)
    
    # Setup dialogs
    setup_dialogs(dp)
    
    logger.info("Bot setup completed")
    return bot, dp


async def setup_database():
    """Initialize database connection."""
    try:
        db_manager.init_engine()
        logger.info("Database connection initialized")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise


@asynccontextmanager
async def lifespan():
    """Application lifespan context manager."""
    try:
        # Startup
        await setup_database()
        logger.info("Application started")
        yield
    finally:
        # Shutdown
        await db_manager.close()
        logger.info("Application shutdown")


async def main():
    # Configure logging
    logging.basicConfig(
        level=logging.INFO if not settings.debug else logging.DEBUG,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    logger.info("Starting Voice Service Bot...")
    
    async with lifespan():
        bot, dp = await setup_bot()
        
        # Start polling
        try:
            await dp.start_polling(bot)
        except Exception as e:
            logger.error(f"Polling error: {e}")
        finally:
            await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())