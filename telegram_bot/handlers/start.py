from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message
from config import logger
from database import get_or_create_user
from database.models import Client
from handlers.show_categories import show_main_menu
from services import subscriptions_check
from sqlalchemy.ext.asyncio import AsyncSession

router = Router()


@router.message(CommandStart())
async def command_start(message: Message, session: AsyncSession) -> None:
    logger.info("/start — получено сообщение от пользователя")

    if not message.from_user:
        logger.warning("message.from_user отсутствует")
        return

    telegram_id = message.from_user.id
    username = message.from_user.username

    logger.info(
        f"Пользователь: telegram_id={telegram_id}, username={username}"
    )

    try:
        user: Client = await get_or_create_user(telegram_id, username, session)
        logger.info(
            f"Пользователь зарегистрирован или найден в БД: id={user.id}"
        )

        is_user_subscribed: bool = await subscriptions_check(message, user)
        if not is_user_subscribed:
            logger.info(f"Пользователь {telegram_id} не подписан — завершение")
            return

        logger.info(
            f"Пользователь {telegram_id} прошёл проверку — отправка главного меню"
        )
        await show_main_menu(message, session)

    except Exception as e:
        logger.error(f"Ошибка в обработке /start: {e}")
