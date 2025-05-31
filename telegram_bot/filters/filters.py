from typing import List, Optional

from aiogram.filters.callback_data import CallbackData
from database.models import CartItem


class CategoryFilter(CallbackData, prefix="category"):
    """
    Кастомный фильтр для навигации по категориям.
    """

    id: int | None = None
    page: int = 1
    parent_id: int | None = None


class SubCategoryFilter(CallbackData, prefix="subcategory"):
    """
    Кастомный фильтр для навигации по подкатегориям.
    """

    id: int | None = None
    page: int = 1
    parent_id: int | None = None


class ProductFilter(CallbackData, prefix="product"):
    """
    Кастомный фильтр для навигации по товарам.
    """

    id: int | None = None
    page: int = 1
    parent_id: int | None = None


class AddToCartFilter(CallbackData, prefix="add_to_cart"):
    id: int


class SetQuantityFilter(CallbackData, prefix="set_quantity"):
    id: int
    quantity: int


class ConfirmAddToCartFilter(CallbackData, prefix="confirm_add_to_cart"):
    id: int
    quantity: int


class RemoveFromCartFilter(CallbackData, prefix="remove_from_cart"):
    user_id: int


class PaymentFilter(CallbackData, prefix="payment"):
    order_id: int
