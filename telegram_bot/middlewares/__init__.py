from aiogram import Dispatcher


def register_middlewares(dp: Dispatcher) -> None:
    from .DatabaseMiddleware import DataBaseSession
    from database.engine import session_maker

    dp.update.middleware(DataBaseSession(session_pool=session_maker))
