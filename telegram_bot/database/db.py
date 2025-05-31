from aiocache import cached
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from datetime import datetime, timezone
from typing import List, Optional
from config import logger
from database.models import (
    Client,
    Category,
    Product,
    CartItem,
    Cart,
    Order,
    OrderItem,
)
from aiogram.types import ShippingAddress


async def get_client_by_telegram_id(
    telegram_id: int, session: AsyncSession
) -> Optional[Client]:
    """Функция для получения клиента по telegram_id."""
    result = await session.execute(
        select(Client).where(Client.telegram_id == telegram_id)
    )
    return result.scalar_one_or_none()


async def get_cart_by_client_id(
    client_id: int, session: AsyncSession, with_items: bool = False
) -> Optional[Cart]:
    """
    Функция для получения корзины клиента,
    с опциональной подгрузкой товаров.
    """
    stmt = select(Cart).where(Cart.client_id == client_id)
    if with_items:
        stmt = stmt.options(selectinload(Cart.items))
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def get_or_create_user(
    telegram_id: int, username: str, session: AsyncSession
) -> Client:
    stmt = select(Client).where(Client.telegram_id == telegram_id)
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()

    if user:
        if user.username != username:
            user.username = username
            await session.commit()
            await session.refresh(user)
        return user

    new_user = Client(
        telegram_id=telegram_id,
        username=username,
        created_at=datetime.now(timezone.utc),
    )
    session.add(new_user)
    await session.commit()
    await session.refresh(new_user)
    return new_user


@cached(ttl=120)
async def get_categories(session: AsyncSession) -> List[Category]:
    stmt = (
        select(Category)
        .where(Category.parent_id.is_(None))
        .order_by(Category.name)
        .options(selectinload(Category.subcategories))
    )
    result = await session.execute(stmt)
    return result.scalars().all()


@cached(ttl=120)
async def get_subcategories(
    category_id: int, session: AsyncSession
) -> List[Category]:
    stmt = (
        select(Category)
        .where(Category.parent_id == category_id)
        .order_by(Category.name)
    )
    result = await session.execute(stmt)
    return result.scalars().all()


@cached(ttl=120)
async def get_products(
    subcategory_id: int, session: AsyncSession
) -> List[Product]:
    stmt = (
        select(Product)
        .where(Product.category_id == subcategory_id)
        .order_by(Product.name)
    )
    result = await session.execute(stmt)
    return result.scalars().all()


@cached(ttl=120)
async def get_product(
    product_id: int, session: AsyncSession
) -> Optional[Product]:
    stmt = select(Product).where(Product.id == product_id)
    result = await session.execute(stmt)
    return result.scalars().first()


async def add_to_cart(
    telegram_id: int,
    product_id: int,
    quantity: int,
    session: AsyncSession,
) -> CartItem:
    async with session.begin():
        client = await get_client_by_telegram_id(telegram_id, session)
        if not client:
            raise ValueError(f"Клиент с telegram_id={telegram_id} не найден")

        cart = await session.scalar(
            select(Cart).where(Cart.client_id == client.id)
        )
        if not cart:
            cart = Cart(
                client_id=client.id, created_at=datetime.now(timezone.utc)
            )
            session.add(cart)
            await session.flush()

        cart_item = await session.scalar(
            select(CartItem)
            .where(
                CartItem.cart_id == cart.id, CartItem.product_id == product_id
            )
            .options(selectinload(CartItem.product))
        )

        if cart_item:
            cart_item.quantity += quantity
        else:
            product = await get_product(product_id, session)
            if not product:
                raise ValueError(f"Товар с product_id={product_id} не найден")
            cart_item = CartItem(
                cart_id=cart.id,
                product_id=product_id,
                quantity=quantity,
                product=product,
            )
            session.add(cart_item)

        await session.flush()
        return cart_item


async def get_cart_items(
    telegram_id: int, session: AsyncSession
) -> List[CartItem]:
    client = await get_client_by_telegram_id(telegram_id, session)
    if not client:
        logger.warning(f"Клиент с ID {telegram_id} не найден")
        return []

    stmt = (
        select(Cart)
        .where(Cart.client_id == client.id)
        .options(selectinload(Cart.items).selectinload(CartItem.product))
    )
    result = await session.execute(stmt)
    cart = result.scalar_one_or_none()

    if not cart:
        logger.info(f"Корзина для клиента {telegram_id} не найдена")
        return []

    logger.info(
        f"Получено {len(cart.items)} товаров из корзины клиента {telegram_id}"
    )
    return cart.items


async def clear_cart_items(telegram_id: int, session: AsyncSession) -> bool:
    async with session.begin():
        client = await get_client_by_telegram_id(telegram_id, session)
        if not client:
            logger.warning(f"Клиент с telegram_id={telegram_id} не найден")
            return False

        cart = await get_cart_by_client_id(client.id, session, with_items=True)
        if not cart:
            logger.info(f"Корзина для клиента {telegram_id} не найдена")
            return False

        # Удаляем товары и корзину
        for item in cart.items:
            await session.delete(item)
        await session.delete(cart)

        logger.info(
            f"Корзина пользователя {telegram_id} была полностью очищена"
        )
        return True


async def create_order_from_cart(
    telegram_id: int,
    address: ShippingAddress,
    session: AsyncSession,
) -> Optional[List[OrderItem]]:
    async with session.begin():
        client = await get_client_by_telegram_id(telegram_id, session)
        if not client:
            logger.warning(f"Клиент с telegram_id={telegram_id} не найден")
            return None

        stmt = (
            select(Cart)
            .where(Cart.client_id == client.id)
            .options(selectinload(Cart.items).selectinload(CartItem.product))
        )
        result = await session.execute(stmt)
        cart = result.scalar_one_or_none()

        if not cart or not cart.items:
            logger.warning(
                f"Корзина пуста или не найдена для клиента {telegram_id}"
            )
            return None

        total_price = sum(
            item.quantity * item.product.price for item in cart.items
        )

        address_str = ", ".join(
            filter(
                None,
                [
                    address.country_code,
                    address.state,
                    address.city,
                    address.street_line1,
                    address.street_line2,
                    address.post_code,
                ],
            )
        )

        new_order = Order(
            client_id=client.id,
            total_price=total_price,
            address=address_str,
            created_at=datetime.now(timezone.utc),
        )
        session.add(new_order)
        await session.flush()

        order_items: List[OrderItem] = []
        for item in cart.items:
            order_item = OrderItem(
                order_id=new_order.id,
                product_id=item.product.id,
                quantity=item.quantity,
                price=item.product.price,
            )
            session.add(order_item)
            order_items.append(order_item)

        # Удаляем корзину и её товары
        for item in cart.items:
            await session.delete(item)
        await session.delete(cart)

        logger.info(f"Создан заказ {new_order.id} для клиента {telegram_id}")
        return order_items
