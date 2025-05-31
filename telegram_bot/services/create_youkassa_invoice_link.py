from aiogram.types import LabeledPrice
from config import YOO_TOKEN, bot, logger


async def create_youkassa_invoice_link(price, user_id):
    logger.info(
        f"Создание ссылки на оплату YouKassa для user_id={user_id} с суммой {price} руб."
    )

    description = "Оплата товаров в корзине"
    price_obj = LabeledPrice(
        label=description,
        amount=int(price * 100),
    )

    try:
        invoice_link = await bot.create_invoice_link(
            title="Оплата",
            description=description,
            payload=f"{user_id}",
            provider_token=YOO_TOKEN,
            currency="rub",
            prices=[price_obj],
            need_shipping_address=True,  # для физических товаров
            is_flexible=False,  # True если стоимость зависит от доставки
        )
        logger.info(f"Ссылка на оплату успешно создана для user_id={user_id}")
        return invoice_link
    except Exception as e:
        logger.error(
            f"Ошибка при создании ссылки на оплату для user_id={user_id}: {e}"
        )
        raise
