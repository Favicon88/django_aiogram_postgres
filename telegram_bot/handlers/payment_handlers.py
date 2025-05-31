import asyncio
from typing import List

from aiogram import F, Router, types
from aiogram.types import ShippingAddress
from config import bot, logger
from database import create_order_from_cart
from database.models import OrderItem
from services import append_order_to_excel
from sqlalchemy.ext.asyncio import AsyncSession

router = Router()


@router.pre_checkout_query()
async def pre_checkout_query(pre_checkout_q: types.PreCheckoutQuery):
    """Подтверждение наличия товара перед оплатой"""

    user_id = pre_checkout_q.from_user.id
    logger.info(
        "Получен pre_checkout_query",
        user_id=user_id,
        invoice_payload=pre_checkout_q.invoice_payload,
    )

    await asyncio.sleep(0.5)  # <-- Критично!
    await bot.answer_pre_checkout_query(pre_checkout_q.id, ok=True)
    logger.info("Ответ на pre_checkout_query отправлен", user_id=user_id)


@router.message(F.successful_payment)
async def successful_payment(
    message: types.Message,
    session: AsyncSession,
):
    """Событие вызывается после успешной оплаты корзины."""

    user_id = int(message.successful_payment.invoice_payload)
    shipping_address: ShippingAddress = (
        message.successful_payment.order_info.shipping_address
    )

    logger.info(
        "Оплата прошла успешно",
        user_id=user_id,
        total_amount=message.successful_payment.total_amount,
    )

    order_items: List[OrderItem] | None = await create_order_from_cart(
        user_id, shipping_address, session
    )
    logger.info(
        "Создание заказа из корзины завершено",
        user_id=user_id,
        items_count=len(order_items) if order_items else 0,
    )

    try:
        await append_order_to_excel(user_id, shipping_address, order_items)
        logger.info("Заказ добавлен в Excel", user_id=user_id)
    except Exception as e:
        logger.error(
            "Ошибка при сохранении заказа в Excel",
            user_id=user_id,
            error=str(e),
        )

    if order_items:
        await message.answer("✅ Спасибо за оплату! Ваш заказ оформлен.")
        logger.info(
            "Пользователю отправлено подтверждение оформления заказа",
            user_id=user_id,
        )
    else:
        await message.answer("Произошла ошибка при оформлении заказа.")
        logger.warning("Заказ не был оформлен", user_id=user_id)
