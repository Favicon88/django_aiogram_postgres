from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from aiocache import cached
from aiogram.types import ShippingAddress
from asyncpg import Pool
from config import logger
from database.models import CartItem, Category, Client, OrderItem, Product
from pydantic import TypeAdapter


async def get_or_create_user(
    telegram_id: int, username: str, pool: Pool
) -> Client:
    """
    Получает или создает пользователя в базе данных.
    """
    async with pool.acquire() as conn:
        # Попытка найти пользователя по telegram_id
        user_record = await conn.fetchrow(
            "SELECT * FROM app_client WHERE telegram_id = $1",
            telegram_id,
        )

        if user_record:
            if user_record["username"] != username:
                await conn.execute(
                    "UPDATE app_client SET username = $1 WHERE telegram_id = $2",
                    username,
                    telegram_id,
                )
                # Перечитываем запись, чтобы получить обновленный username
                user_record = await conn.fetchrow(
                    "SELECT * FROM app_client WHERE telegram_id = $1",
                    telegram_id,
                )
            return TypeAdapter(Client).validate_python(dict(user_record))
        else:
            # Пользователь не найден, создаем нового
            new_user_record: Dict = await conn.fetchrow(
                """
                INSERT INTO app_client (telegram_id, username, created_at) 
                VALUES ($1, $2, $3) RETURNING *
                """,
                telegram_id,
                username,
                datetime.utcnow(),
            )
            return TypeAdapter(Client).validate_python(dict(new_user_record))


@cached(ttl=120)
async def get_categories(
    pool: Pool,
) -> List[Category]:
    """
    Возвращает список основных категорий из базы данных.
    """
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT *
            FROM app_category
            WHERE parent_id IS NULL
            ORDER BY name;
            """
        )

    if not rows:
        return

    row_dicts = [dict(row) for row in rows]

    return TypeAdapter(List[Category]).validate_python(row_dicts)


@cached(ttl=120)
async def get_subcategories(
    category_id: int,
    pool: Pool,
) -> List[Category]:
    """
    Возвращает подкатегории указанной категории.
    """
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT *
            FROM app_category
            WHERE parent_id = $1
            ORDER BY name;
            """,
            category_id,
        )

    if not rows:
        return
    row_dicts = [dict(row) for row in rows]

    return TypeAdapter(List[Category]).validate_python(row_dicts)


@cached(ttl=120)
async def get_products(
    subcategory_id: int,
    pool: Pool,
) -> List[Product]:
    """
    Возвращает список товаров из подкатегории
    """
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT *
            FROM app_product
            WHERE category_id = $1
            ORDER BY name;
            """,
            subcategory_id,
        )

    if not rows:
        return
    row_dicts = [dict(row) for row in rows]

    return TypeAdapter(List[Product]).validate_python(row_dicts)


@cached(ttl=120)
async def get_product(
    product_id: int,
    pool: Pool,
) -> Product | None:
    """
    Возвращает информацию о товаре по product_id.
    """
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            SELECT *
            FROM app_product
            WHERE id = $1;
            """,
            product_id,
        )

    if row is None:
        return

    return TypeAdapter(Product).validate_python(dict(row))


async def add_to_cart(
    telegram_id: int, product_id: int, quantity: int, pool: Pool
) -> CartItem:
    """Добавляет товар в корзину, все операции транзакцией."""
    async with pool.acquire() as conn:
        async with conn.transaction():
            client = await conn.fetchrow(
                "SELECT id FROM app_client WHERE telegram_id = $1", telegram_id
            )
            if not client:
                logger.error(f"Клиент с ID {telegram_id} не найден")
                raise ValueError("Клиент не найден")
            client_id = client["id"]

            cart = await conn.fetchrow(
                "SELECT id FROM app_cart WHERE client_id = $1", client_id
            )
            if not cart:
                cart = await conn.fetchrow(
                    "INSERT INTO app_cart (client_id, created_at) VALUES ($1, NOW()) RETURNING id",
                    client_id,
                )
                logger.info(f"Создана новая корзина для клиента {telegram_id}")
            cart_id = cart["id"]

            cart_item = await conn.fetchrow(
                "SELECT id, quantity FROM app_cartitem WHERE cart_id = $1 AND product_id = $2",
                cart_id,
                product_id,
            )

            if cart_item:
                new_quantity = cart_item["quantity"] + quantity
                await conn.execute(
                    "UPDATE app_cartitem SET quantity = $1 WHERE id = $2",
                    new_quantity,
                    cart_item["id"],
                )
                cart_item_id = cart_item["id"]
            else:
                new_item = await conn.fetchrow(
                    "INSERT INTO app_cartitem (cart_id, product_id, quantity) VALUES ($1, $2, $3) RETURNING id, quantity",
                    cart_id,
                    product_id,
                    quantity,
                )
                cart_item_id = new_item["id"]
                new_quantity = new_item["quantity"]

            # Получаем данные товара
            product_row = await conn.fetchrow(
                "SELECT * FROM app_product WHERE id = $1",
                product_id,
            )
            if not product_row:
                logger.error(f"Продукт с ID {product_id} не найден")
                raise ValueError("Товар не найден")

            product = Product(**dict(product_row))

            return CartItem(
                id=cart_item_id, product=product, quantity=new_quantity
            )


async def get_cart_items(
    telegram_id: int, pool: Pool
) -> List[CartItem] | None:
    """
    Получает список товаров в корзине пользователя по telegram_id.
    """
    async with pool.acquire() as conn:
        async with conn.transaction():
            client = await conn.fetchrow(
                "SELECT id FROM app_client WHERE telegram_id = $1", telegram_id
            )
            if not client:
                logger.warning(f"Клиент с ID {telegram_id} не найден")
                return []

            client_id = client["id"]

            cart = await conn.fetchrow(
                "SELECT id FROM app_cart WHERE client_id = $1", client_id
            )
            if not cart:
                logger.info(f"Корзина для клиента {telegram_id} не найдена")
                return []

            cart_id = cart["id"]

            rows = await conn.fetch(
                """
                SELECT 
                    ci.id AS cart_item_id,
                    ci.quantity,
                    p.id AS product_id,
                    p.name,
                    p.price
                FROM app_cartitem ci
                JOIN app_product p ON ci.product_id = p.id
                WHERE ci.cart_id = $1
                """,
                cart_id,
            )

            items: List[CartItem] = []
            for row in rows:
                product = Product(
                    id=row["product_id"], name=row["name"], price=row["price"]
                )
                cart_item = CartItem(
                    id=row["cart_item_id"],
                    product=product,
                    quantity=row["quantity"],
                )
                items.append(cart_item)

            logger.info(
                f"Получено {len(items)} товаров из корзины клиента {telegram_id}"
            )
            return items


async def clear_cart_items(telegram_id: int, pool: Pool) -> bool:
    """
    Полностью очищает корзину пользователя по его telegram_id:
    - Удаляет все товары из app_cartitem
    - Удаляет саму корзину из app_cart
    """

    async with pool.acquire() as conn:
        async with conn.transaction():
            client = await conn.fetchrow(
                "SELECT id FROM app_client WHERE telegram_id = $1",
                telegram_id,
            )
            if not client:
                logger.warning(f"Клиент с telegram_id={telegram_id} не найден")
                return False

            cart = await conn.fetchrow(
                "SELECT id FROM app_cart WHERE client_id = $1",
                client["id"],
            )
            if not cart:
                logger.info(f"Корзина для клиента {telegram_id} не найдена")
                return False

            cart_id = cart["id"]

            # Удаляем все товары из корзины
            await conn.execute(
                "DELETE FROM app_cartitem WHERE cart_id = $1",
                cart_id,
            )

            # Удаляем саму корзину
            await conn.execute(
                "DELETE FROM app_cart WHERE id = $1",
                cart_id,
            )

            logger.info(
                f"Корзина пользователя {telegram_id} была полностью очищена"
            )
            return True


async def create_order_from_cart(
    telegram_id: int,
    address: ShippingAddress,
    pool: Pool,
) -> Optional[List[OrderItem]]:
    async with pool.acquire() as conn:
        async with conn.transaction():
            client = await conn.fetchrow(
                "SELECT id FROM app_client WHERE telegram_id = $1", telegram_id
            )
            if not client:
                logger.warning(f"Клиент с telegram_id={telegram_id} не найден")
                return None

            client_id = client["id"]

            cart = await conn.fetchrow(
                "SELECT id FROM app_cart WHERE client_id = $1", client_id
            )
            if not cart:
                logger.warning(f"Корзина клиента {telegram_id} не найдена")
                return None

            cart_id = cart["id"]

            cart_items = await conn.fetch(
                """
                SELECT 
                    ci.product_id,
                    ci.quantity,
                    p.id, p.name, p.price, p.category_id, p.description, p.photo
                FROM app_cartitem ci
                JOIN app_product p ON ci.product_id = p.id
                WHERE ci.cart_id = $1
                """,
                cart_id,
            )

            if not cart_items:
                logger.warning(f"Корзина пуста для клиента {telegram_id}")
                return None

            total_price = sum(
                row["quantity"] * row["price"] for row in cart_items
            )

            order_row = await conn.fetchrow(
                """
                INSERT INTO app_order (client_id, total_price, address, created_at)
                VALUES ($1, $2, $3, $4)
                RETURNING id
                """,
                client_id,
                total_price,
                address.model_dump_json(),
                datetime.utcnow(),
            )
            order_id = order_row["id"]

            for item in cart_items:
                await conn.execute(
                    """
                    INSERT INTO app_orderitem (order_id, product_id, quantity, price)
                    VALUES ($1, $2, $3, $4)
                    """,
                    order_id,
                    item["product_id"],
                    item["quantity"],
                    item["price"],
                )

            await conn.execute(
                "DELETE FROM app_cartitem WHERE cart_id = $1", cart_id
            )
            await conn.execute("DELETE FROM app_cart WHERE id = $1", cart_id)

            logger.info(f"Создан заказ {order_id} для клиента {telegram_id}")

            order_items: List[OrderItem] = []

            for row in cart_items:
                product = TypeAdapter(Product).validate_python(dict(row))

                order_item = OrderItem(
                    id=row["product_id"],
                    product=product,
                    quantity=row["quantity"],
                    price=row["price"],
                )
                order_items.append(order_item)

            return order_items
