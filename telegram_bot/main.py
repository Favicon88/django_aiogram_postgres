import asyncio

from config import bot, dp, logger
from handlers import get_handlers_router
from keyboards.default_commands import set_default_commands
from middlewares import register_middlewares


async def on_startup() -> None:

    logger.info("Starting bot")
    register_middlewares(dp)
    dp.include_router(get_handlers_router())
    await set_default_commands(bot)


async def on_shutdown() -> None:
    await dp.storage.close()
    await dp.fsm.storage.close()
    logger.info("bot stopped")


async def main():
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


if __name__ == "__main__":
    asyncio.run(main())
