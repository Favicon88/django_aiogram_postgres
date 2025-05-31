from typing import Dict

from aiogram.types import Message
from config import CHANNEL_ID, GROUP_ID, bot, logger
from database.models import Client
from keyboards import get_subscription_keyboard
from locales.constants_text_ru import SUBSCRIBE_TO_OUR_CHANNELS


async def subscription_check(chat_id: int, user_id: int) -> bool:
    logger.info(f"Проверка подписки пользователя {user_id} на чат {chat_id}")
    try:
        chat_member = await bot.get_chat_member(
            chat_id=chat_id, user_id=user_id
        )
        is_subscribed = chat_member.status in (
            "member",
            "administrator",
            "creator",
        )
        logger.info(
            f"Пользователь {user_id} подписан на чат {chat_id}: {is_subscribed}"
        )
        return is_subscribed
    except Exception as e:
        logger.error(
            f"Ошибка проверки подписки пользователя {user_id} на чат {chat_id}: {e}"
        )
        return False


async def subscriptions_check(message: Message, user: Client) -> bool:
    logger.info(
        f"Проверка подписки пользователя {user.telegram_id} на каналы и группы"
    )
    is_channel_member = await subscription_check(
        chat_id=CHANNEL_ID, user_id=user.telegram_id
    )
    is_group_member = await subscription_check(
        chat_id=GROUP_ID, user_id=user.telegram_id
    )

    if not is_channel_member or not is_group_member:
        logger.info(
            f"Пользователь {user.telegram_id} не подписан на необходимые каналы/группы"
        )
        subscription_keyboard = await get_subscription_keyboard()
        await message.answer(
            SUBSCRIBE_TO_OUR_CHANNELS, reply_markup=subscription_keyboard
        )
    else:
        logger.info(
            f"Пользователь {user.telegram_id} подписан на все необходимые каналы и группы"
        )

    return is_channel_member and is_group_member
