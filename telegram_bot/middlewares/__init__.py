from aiogram import Dispatcher


def register_middlewares(dp: Dispatcher) -> None:
    from .DatabaseMiddleware import DatabaseMiddleware

    dp.update.outer_middleware(DatabaseMiddleware())
