import asyncpg
from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message
from config import logger
from database import get_or_create_user
from database.models import Client
from handlers.show_categories import show_main_menu
from services import subscriptions_check

router = Router()


@router.message(CommandStart())
async def command_start(message: Message, pool: asyncpg.Pool) -> None:
    """
    Обрабатывает команду /start.
    Проверяет пользователя в БД, если его нет — регистрирует,
    и отправляет приветственное сообщение с главным меню.
    """

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
        user: Client = await get_or_create_user(telegram_id, username, pool)
        logger.info(
            f"Пользователь зарегистрирован или найден в БД: id={user.id}"
        )
    except Exception as e:
        logger.error(f"Ошибка при получении/создании пользователя: {e}")
        return

    try:
        is_user_subscribed: bool = await subscriptions_check(message, user)
    except Exception as e:
        logger.error(f"Ошибка при проверке подписки: {e}")
        return

    if not is_user_subscribed:
        logger.info(f"Пользователь {telegram_id} не подписан — завершение")
        return

    logger.info(
        f"Пользователь {telegram_id} прошёл проверку — отправка главного меню"
    )

    try:
        await show_main_menu(message, pool)
    except Exception as e:
        logger.error(f"Ошибка при отправке главного меню: {e}")
