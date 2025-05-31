from datetime import datetime, timezone

from sqlalchemy import (
    Integer,
    String,
    DateTime,
    ForeignKey,
    Text,
    Numeric,
)
from sqlalchemy.orm import relationship, DeclarativeBase, Mapped, mapped_column
from typing import Optional, List


class Base(DeclarativeBase):
    """Базовый класс для всех моделей SQLAlchemy."""

    pass


class Client(Base):
    """
    Модель клиента, соответствующая Django модели Client.
    Хранит информацию о пользователе Telegram.
    """

    __tablename__ = "app_client"

    id: Mapped[int] = mapped_column(primary_key=True)
    telegram_id: Mapped[int] = mapped_column(Integer, unique=True, index=True)
    username: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    carts: Mapped[Optional["Cart"]] = relationship(
        back_populates="client", uselist=False
    )
    orders: Mapped[List["Order"]] = relationship(back_populates="client")


class Category(Base):
    """
    Модель категории и подкатегории товаров, соответствующая Django модели Category.
    """

    __tablename__ = "app_category"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    parent_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("app_category.id"),
        nullable=True,
    )
    parent: Mapped[Optional["Category"]] = relationship(
        remote_side=[id], back_populates="subcategories"
    )
    subcategories: Mapped[List["Category"]] = relationship(
        back_populates="parent"
    )
    products: Mapped[List["Product"]] = relationship(back_populates="category")


class Product(Base):
    """
    Модель товара, соответствующая Django модели Product.
    """

    __tablename__ = "app_product"

    id: Mapped[int] = mapped_column(primary_key=True)
    category_id: Mapped[int] = mapped_column(ForeignKey("app_category.id"))
    name: Mapped[str] = mapped_column(String(200))
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    price: Mapped[float] = mapped_column(Numeric(10, 2))
    photo: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    category: Mapped["Category"] = relationship(back_populates="products")
    cart_items: Mapped[List["CartItem"]] = relationship(
        back_populates="product"
    )
    order_items: Mapped[List["OrderItem"]] = relationship(
        back_populates="product"
    )


class Cart(Base):
    """
    Модель корзины пользователя, соответствующая Django модели Cart.
    """

    __tablename__ = "app_cart"

    id: Mapped[int] = mapped_column(primary_key=True)
    client_id: Mapped[int] = mapped_column(
        ForeignKey("app_client.id"), unique=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    client: Mapped["Client"] = relationship(back_populates="carts")
    items: Mapped[List["CartItem"]] = relationship(
        back_populates="cart", cascade="all, delete-orphan"
    )


class CartItem(Base):
    """
    Модель товаров в корзине, соответствующая Django модели CartItem.
    """

    __tablename__ = "app_cartitem"

    id: Mapped[int] = mapped_column(primary_key=True)
    cart_id: Mapped[int] = mapped_column(ForeignKey("app_cart.id"))
    product_id: Mapped[int] = mapped_column(ForeignKey("app_product.id"))
    quantity: Mapped[int] = mapped_column(Integer, default=1)

    cart: Mapped["Cart"] = relationship(back_populates="items")
    product: Mapped["Product"] = relationship(back_populates="cart_items")


class Order(Base):
    """
    Модель оформленного заказа клиента, соответствующая Django модели Order.
    """

    __tablename__ = "app_order"
    id: Mapped[int] = mapped_column(primary_key=True)
    client_id: Mapped[int] = mapped_column(ForeignKey("app_client.id"))
    address: Mapped[str] = mapped_column(String(255), nullable=True)
    total_price: Mapped[float] = mapped_column(Numeric(20, 2), default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    client: Mapped["Client"] = relationship(back_populates="orders")
    items: Mapped[List["OrderItem"]] = relationship(
        back_populates="order", cascade="all, delete-orphan"
    )


class OrderItem(Base):
    """
    Модель товара в составе заказа клиента, соответствующая Django модели OrderItem.
    """

    __tablename__ = "app_orderitem"

    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("app_order.id"))
    product_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("app_product.id"),
        nullable=True,
    )
    quantity: Mapped[int] = mapped_column(Integer, default=1)
    price: Mapped[float] = mapped_column(Numeric(20, 2), default=0)

    order: Mapped["Order"] = relationship(back_populates="items")
    product: Mapped[Optional["Product"]] = relationship(
        back_populates="order_items"
    )
