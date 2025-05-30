from typing import List

from aiogram import F, Router
from aiogram.types import CallbackQuery
from asyncpg import Pool
from config import logger
from database import add_to_cart, clear_cart_items, get_cart_items
from database.models import CartItem
from filters import (
    AddToCartFilter,
    ConfirmAddToCartFilter,
    RemoveFromCartFilter,
    SetQuantityFilter,
)
from handlers.show_categories import show_main_menu
from keyboards import (
    get_cart_items_keyboard,
    get_main_menu_keyboard,
    get_set_quantity_keyboard,
    get_start_order_keyboard,
)
from locales.constants_text_ru import ITEMS_IN_CART
from services import create_youkassa_invoice_link

router = Router()


@router.callback_query(AddToCartFilter.filter())
async def add_to_cart_handler(
    call: CallbackQuery, callback_data: AddToCartFilter
):
    logger.info(
        "Выбор количества товара",
        user_id=call.from_user.id,
        product_id=callback_data.id,
    )
    keyboard = await get_set_quantity_keyboard(
        callback_data.id, 1, callback_data
    )

    await call.message.edit_caption(
        "Выберите количество товара 👇🏼", reply_markup=keyboard
    )


@router.callback_query(SetQuantityFilter.filter())
async def set_quantity_handler(
    call: CallbackQuery, callback_data: SetQuantityFilter
):
    logger.info(
        "Изменение количества товара",
        user_id=call.from_user.id,
        product_id=callback_data.id,
        quantity=callback_data.quantity,
    )
    quantity = callback_data.quantity

    keyboard = await get_set_quantity_keyboard(
        callback_data.id, quantity, callback_data
    )
    await call.message.edit_reply_markup(reply_markup=keyboard)


@router.callback_query(ConfirmAddToCartFilter.filter())
async def confirm_add_to_cart_handler(
    call: CallbackQuery, pool: Pool, callback_data: ConfirmAddToCartFilter
):
    product_id = callback_data.id
    quantity = callback_data.quantity
    user_id = call.from_user.id

    logger.info(
        "Подтверждение добавления в корзину",
        user_id=user_id,
        product_id=product_id,
        quantity=quantity,
    )
    await add_to_cart(user_id, product_id, quantity, pool)
    keyboard = await get_main_menu_keyboard()
    await call.message.delete()
    await call.message.answer(
        "✅ Товар добавлен в корзину!", reply_markup=keyboard
    )


@router.callback_query(F.data == "cart_handler")
async def cart_handler(call: CallbackQuery, pool: Pool):
    user_id = call.from_user.id
    logger.info("Пользователь открыл корзину", user_id=user_id)

    try:
        cart_items: List[CartItem] | None = await get_cart_items(user_id, pool)
    except Exception as e:
        logger.exception("Ошибка получения корзины", user_id=user_id)
        await call.message.answer(
            "Произошла ошибка при получении корзины. Попробуйте позже."
        )
        return

    if not cart_items:
        logger.info("Корзина пуста", user_id=user_id)
        await call.message.answer("В корзине нет товаров.")
        return

    keyboard = await get_cart_items_keyboard(cart_items, user_id)
    cart_text = ITEMS_IN_CART
    for item in cart_items:
        cart_text += f"\n✅ {item.product.name} x {item.quantity} шт. = {item.quantity*item.product.price} р.\n"

    try:
        await call.message.edit_text(cart_text, reply_markup=keyboard)
    except Exception:
        logger.exception("Ошибка при отображении корзины", user_id=user_id)
        await call.message.answer("Произошла ошибка при отображении корзины.")


@router.callback_query(F.data == "order_cart_items")
async def start_order(call: CallbackQuery, pool: Pool):
    user_id = call.from_user.id
    logger.info("Начало оформления заказа", user_id=user_id)

    try:
        cart_items: List[CartItem] | None = await get_cart_items(user_id, pool)
    except Exception:
        logger.exception(
            "Ошибка получения корзины для оформления", user_id=user_id
        )
        await call.message.answer(
            "Произошла ошибка при получении корзины. Попробуйте позже."
        )
        return

    if not cart_items:
        logger.info("Оформление невозможно — корзина пуста", user_id=user_id)
        await call.answer("Ваша корзина пуста")
        return

    price = sum(item.quantity * item.product.price for item in cart_items)
    invoice_link = await create_youkassa_invoice_link(price, user_id)
    logger.info(
        "Сформирована ссылка на оплату",
        user_id=user_id,
        price=price,
        invoice_link=invoice_link,
    )
    keyboard = await get_start_order_keyboard(invoice_link)
    await call.message.edit_reply_markup(reply_markup=keyboard)


@router.callback_query(RemoveFromCartFilter.filter())
async def clear_cart_handler(
    call: CallbackQuery, pool: Pool, callback_data: RemoveFromCartFilter
):
    logger.info("Очистка корзины", user_id=callback_data.user_id)
    await clear_cart_items(callback_data.user_id, pool)
    await call.message.edit_text("Ваша корзина теперь пуста")
    await show_main_menu(call, pool)


@router.callback_query(F.data == "none")
async def noop_callback(call: CallbackQuery):
    logger.debug("Нажата заглушка-кнопка", user_id=call.from_user.id)
    await call.answer()
