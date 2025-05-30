import os
from typing import List

from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import CallbackQuery, FSInputFile, InputMediaPhoto, Message
from asyncpg import Pool
from config import logger
from database import (
    get_categories,
    get_product,
    get_products,
    get_subcategories,
)
from database.models import Category, Product
from filters import CategoryFilter, ProductFilter, SubCategoryFilter
from keyboards import (
    get_add_to_cart_keyboard,
    get_catalog_keyboard,
    get_main_menu_keyboard,
)
from locales.constants_text_ru import (
    PRODUCT_DESCRIPTION,
    PRODUCT_NOT_FOUND,
    RETURN,
    SELECT_CATEGORY,
    SELECT_PRODUCT,
    SELECT_SUBCATEGORY,
)

router = Router()


@router.callback_query(F.data == "show_main_menu")
async def show_main_menu(call: Message | CallbackQuery, pool: Pool):
    message = call.message if isinstance(call, CallbackQuery) else call
    keyboard = await get_main_menu_keyboard()
    try:
        await message.edit_text("Главное меню", reply_markup=keyboard)
        logger.info("Показано главное меню", user_id=call.from_user.id)
    except Exception:
        await message.answer("Главное меню", reply_markup=keyboard)
        logger.warning(
            "Не удалось отредактировать сообщение — отправка нового",
            user_id=call.from_user.id,
        )


@router.callback_query(CategoryFilter.filter())
async def show_categories(
    call: Message | CallbackQuery,
    pool: Pool,
    callback_data: CategoryFilter | None = None,
):
    message = call.message if isinstance(call, CallbackQuery) else call

    categories: List[Category] | None = await get_categories(pool)
    if not categories:
        await message.answer("Категории пока не добавлены.")
        logger.warning("Категории не найдены", user_id=call.from_user.id)
        return

    if not callback_data or not callback_data.id:
        keyboard = await get_catalog_keyboard(
            "category",
            categories,
            return_text=RETURN,
            return_callback="show_main_menu",
        )
        try:
            await message.edit_text(SELECT_CATEGORY, reply_markup=keyboard)
            logger.info(
                "Отображён список категорий", user_id=call.from_user.id
            )
        except Exception:
            await message.answer(SELECT_CATEGORY, reply_markup=keyboard)
            logger.warning(
                "Не удалось отредактировать сообщение при показе категорий",
                user_id=call.from_user.id,
            )
    else:
        subcategories = await get_subcategories(callback_data.id, pool)
        keyboard = await get_catalog_keyboard(
            "subcategory",
            subcategories,
            callback_data.page,
            callback_data.id,
            RETURN,
            CategoryFilter().pack(),
        )
        await message.edit_text(SELECT_SUBCATEGORY, reply_markup=keyboard)
        logger.info(
            "Отображены подкатегории",
            user_id=call.from_user.id,
            category_id=callback_data.id,
        )


@router.callback_query(SubCategoryFilter.filter())
async def show_subcategories(
    call: CallbackQuery, pool: Pool, callback_data: SubCategoryFilter
):
    subcategory_id = callback_data.id
    page = callback_data.page
    category_id = callback_data.parent_id

    if not subcategory_id and category_id:
        subcategories = await get_subcategories(category_id, pool)
        keyboard = await get_catalog_keyboard(
            "subcategory",
            subcategories,
            page,
            category_id,
            RETURN,
            CategoryFilter().pack(),
        )
        await call.message.edit_text(SELECT_SUBCATEGORY, reply_markup=keyboard)
        logger.info(
            "Отображены подкатегории",
            user_id=call.from_user.id,
            category_id=category_id,
        )
    elif not subcategory_id and not category_id:
        categories = await get_categories(pool)
        keyboard = await get_catalog_keyboard(
            "category",
            categories,
            page=1,
            return_text=RETURN,
            return_callback=ProductFilter().pack(),
        )
        await call.message.edit_text(SELECT_CATEGORY, reply_markup=keyboard)
        logger.info("Отображён корень каталога", user_id=call.from_user.id)
    else:
        products = await get_products(subcategory_id, pool)
        keyboard = await get_catalog_keyboard(
            "product",
            products,
            1,
            subcategory_id,
            RETURN,
            SubCategoryFilter(parent_id=category_id).pack(),
        )
        try:
            await call.message.edit_text(
                SELECT_SUBCATEGORY, reply_markup=keyboard
            )
            logger.info(
                "Отображён список товаров подкатегории",
                user_id=call.from_user.id,
                subcategory_id=subcategory_id,
            )
        except TelegramBadRequest as e:
            if "no text in the message to edit" in str(e):
                await call.message.delete()
                await call.message.answer(
                    SELECT_PRODUCT, reply_markup=keyboard
                )
                logger.warning(
                    "Сообщение не имело текста — заменено новым",
                    user_id=call.from_user.id,
                )


@router.callback_query(ProductFilter.filter())
async def show_products(
    call: CallbackQuery, pool: Pool, callback_data: ProductFilter
):
    product_id = callback_data.id
    page = callback_data.page
    subcategory_id = callback_data.parent_id

    if not product_id and subcategory_id:
        products = await get_products(subcategory_id, pool)
        keyboard = await get_catalog_keyboard(
            "product",
            products,
            page,
            subcategory_id,
            RETURN,
            SubCategoryFilter().pack(),
        )
        await call.message.edit_text(SELECT_PRODUCT, reply_markup=keyboard)
        logger.info(
            "Отображён список товаров",
            user_id=call.from_user.id,
            subcategory_id=subcategory_id,
        )
    elif not product_id and not subcategory_id:
        categories = await get_categories(pool)
        keyboard = await get_catalog_keyboard("category", categories, page=1)
        await call.message.edit_text(SELECT_CATEGORY, reply_markup=keyboard)
        logger.info("Возврат к списку категорий", user_id=call.from_user.id)
    else:
        product: Product | None = await get_product(product_id, pool)
        if not product:
            await call.message.answer(PRODUCT_NOT_FOUND)
            logger.warning(
                "Товар не найден",
                user_id=call.from_user.id,
                product_id=product_id,
            )
            return

        keyboard = await get_add_to_cart_keyboard(product_id, callback_data)

        if product.photo and os.path.exists(product.photo):
            media = InputMediaPhoto(
                media=FSInputFile(product.photo),
                caption=PRODUCT_DESCRIPTION.format(
                    product.name, product.description, product.price
                ),
            )
            await call.message.edit_media(
                media=media, reply_markup=keyboard, parse_mode="HTML"
            )
            logger.info(
                "Показан товар с изображением",
                user_id=call.from_user.id,
                product_id=product_id,
            )
        else:
            await call.message.answer("Изображение не найдено!")
            logger.warning(
                "Изображение товара не найдено",
                user_id=call.from_user.id,
                product_id=product_id,
            )
