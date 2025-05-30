import math
from typing import Dict, List

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from config import CHANNEL_URL, GROUP_URL
from constants import BUTTONS_PER_PAGE
from database.models import CartItem
from filters import (
    AddToCartFilter,
    CategoryFilter,
    ConfirmAddToCartFilter,
    ProductFilter,
    RemoveFromCartFilter,
    SetQuantityFilter,
    SubCategoryFilter,
)
from locales.constants_text_ru import (
    CHECK_SUBSCRIBE_TEXT,
    ITEMS_IN_CART,
    OUR_CHANNEL,
    OUR_GROUP,
    RETURN,
)
from utils import Pagination


async def get_subscription_keyboard():
    """Инлайн клавиатура для подписки на каналы и группы."""

    buttons = [
        [
            InlineKeyboardButton(
                text=OUR_CHANNEL,
                url=CHANNEL_URL,
            ),
        ],
        [
            InlineKeyboardButton(
                text=OUR_GROUP,
                url=GROUP_URL,
            ),
        ],
        [
            InlineKeyboardButton(
                text=CHECK_SUBSCRIBE_TEXT,
                callback_data="check_subscription_to_channels",
            ),
        ],
    ]
    subscription_keyboard = InlineKeyboardBuilder(markup=buttons)

    return subscription_keyboard.as_markup()


async def get_catalog_keyboard(
    level: str,
    items: List,
    page: int = 1,
    parent_id: int = None,
    return_text: str = None,
    return_callback: str = None,
):
    """Создает клавиатуру для каталога категорий, подкатегорий, товаров"""

    pagination = Pagination(level, items, page)
    keyboard = InlineKeyboardBuilder()

    for item in pagination.get_page():
        if level == "subcategory":
            call_data = SubCategoryFilter(
                level=level, id=item.id, page=1, parent_id=parent_id
            )
        elif level == "product":
            call_data = ProductFilter(
                level=level, id=item.id, page=1, parent_id=parent_id
            )
        else:
            call_data = CategoryFilter(level=level, id=item.id, page=1)

        keyboard.add(
            InlineKeyboardButton(
                text=item.name, callback_data=call_data.pack()
            )
        )

    keyboard.adjust(1)

    pagination_btns = []
    if pagination.has_previous():
        if level == "subcategory":
            pagination_prev = SubCategoryFilter(
                level=level,
                id=None,
                page=pagination.page - 1,
                category_id=parent_id,
            )
        elif level == "product":
            pagination_prev = ProductFilter(
                level=level,
                id=None,
                page=pagination.page - 1,
                parent_id=parent_id,
            )
        else:
            pagination_prev = CategoryFilter(
                level=level, id=None, page=pagination.page - 1
            )

        pagination_btns.append(
            InlineKeyboardButton(
                text="⬅️", callback_data=pagination_prev.pack()
            )
        )
    else:
        pagination_btns.append(
            InlineKeyboardButton(text="⬅️", callback_data="none")
        )
    pagination_btns.append(
        InlineKeyboardButton(
            text=f"{page}/{pagination.pages}",
            callback_data="none",
        )
    )

    if pagination.has_next():
        if level == "subcategory":
            pagination_next = SubCategoryFilter(
                id=None, page=pagination.page + 1, category_id=parent_id
            )
        elif level == "product":
            pagination_next = ProductFilter(
                id=None, page=pagination.page + 1, parent_id=parent_id
            )
        else:
            pagination_next = CategoryFilter(id=None, page=pagination.page + 1)

        pagination_btns.append(
            InlineKeyboardButton(
                text="➡️", callback_data=pagination_next.pack()
            )
        )
    else:
        pagination_btns.append(
            InlineKeyboardButton(text="➡️", callback_data="none")
        )

    if pagination_btns and pagination.pages > 1:
        keyboard.row(*pagination_btns)

    if return_text and return_callback:
        keyboard.row(
            InlineKeyboardButton(
                text=return_text, callback_data=return_callback
            )
        )

    return keyboard.as_markup()


async def get_main_menu_keyboard():
    """Инлайн клавиатура главного меню."""

    buttons = [
        [
            InlineKeyboardButton(
                text="Каталог",
                callback_data=CategoryFilter().pack(),
            ),
        ],
        [
            InlineKeyboardButton(
                text="Корзина",
                callback_data="cart_handler",
            ),
        ],
        [
            InlineKeyboardButton(
                text="FAQ",
                callback_data="faq_handler",
            ),
        ],
    ]
    keyboard = InlineKeyboardBuilder(markup=buttons)

    return keyboard.as_markup()


async def get_add_to_cart_keyboard(
    product_id: int, callback_data: ProductFilter
):
    """Инлайн клавиатура для добавления товара."""

    back_callback = SubCategoryFilter(
        id=callback_data.parent_id,
        parent_id=callback_data.parent_id,
        page=callback_data.page,
    ).pack()

    buttons = [
        [
            InlineKeyboardButton(
                text="Добавить в корзину",
                callback_data=AddToCartFilter(id=product_id).pack(),
            ),
        ],
        [
            InlineKeyboardButton(
                text=RETURN,
                callback_data=back_callback,
            ),
        ],
    ]
    keyboard = InlineKeyboardBuilder(markup=buttons)

    return keyboard.as_markup()


async def get_set_quantity_keyboard(
    product_id: int, quantity: int, callback_data: AddToCartFilter
):
    """Инлайн клавиатура для добавления товара."""

    back_callback = ProductFilter(
        id=callback_data.id,
        parent_id=callback_data.id,
    ).pack()

    buttons = [
        [
            InlineKeyboardButton(
                text="-",
                callback_data=SetQuantityFilter(
                    id=product_id, quantity=quantity - 1
                ).pack(),
            ),
            InlineKeyboardButton(
                text=f"{quantity}",
                callback_data="none",
            ),
            InlineKeyboardButton(
                text="+",
                callback_data=SetQuantityFilter(
                    id=product_id, quantity=quantity + 1
                ).pack(),
            ),
        ],
        [
            InlineKeyboardButton(
                text="Подтвердить",
                callback_data=ConfirmAddToCartFilter(
                    id=product_id, quantity=quantity
                ).pack(),
            ),
        ],
        [
            InlineKeyboardButton(
                text=RETURN,
                callback_data=back_callback,
            ),
        ],
    ]
    keyboard = InlineKeyboardBuilder(markup=buttons)

    return keyboard.as_markup()


async def get_cart_items_keyboard(cart_items: List[CartItem], user_id=int):
    """Инлайн клавиатура для корзины с товарами."""

    buttons = [
        [
            InlineKeyboardButton(
                text=f"✅ Оформить заказ",
                callback_data="order_cart_items",
            )
        ],
        [
            InlineKeyboardButton(
                text=f"❌ Удалить корзину",
                callback_data=RemoveFromCartFilter(user_id=user_id).pack(),
            )
        ],
        [
            InlineKeyboardButton(
                text=RETURN,
                callback_data="show_main_menu",
            ),
        ],
    ]
    keyboard = InlineKeyboardBuilder(markup=buttons)

    return keyboard.as_markup()


async def get_start_order_keyboard(invoice_link):
    """Инлайн клавиатура для корзины с товарами."""

    buttons = [
        [InlineKeyboardButton(text="Оплатить 💳", url=invoice_link)],
        [
            InlineKeyboardButton(
                text=RETURN,
                callback_data="show_main_menu",
            ),
        ],
    ]
    keyboard = InlineKeyboardBuilder(markup=buttons)

    return keyboard.as_markup()


async def get_to_main_menu_keyboard():
    """Инлайн кнопка возврата на главное меню."""

    buttons = [
        [
            InlineKeyboardButton(
                text=RETURN,
                callback_data="show_main_menu",
            ),
        ],
    ]
    keyboard = InlineKeyboardBuilder(markup=buttons)

    return keyboard.as_markup()
