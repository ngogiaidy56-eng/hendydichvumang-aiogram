"""Create the aiogram v3 Bot and Dispatcher."""
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from bot.handlers.admin import router as admin_router
from bot.handlers.proxy import router as proxy_router
from config import Settings


def create_bot_dispatcher(settings: Settings) -> tuple[Bot, Dispatcher]:
    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dispatcher = Dispatcher(storage=MemoryStorage())
    dispatcher.include_router(proxy_router)
    dispatcher.include_router(admin_router)
    return bot, dispatcher
