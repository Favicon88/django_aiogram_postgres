from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class Client(BaseModel):
    id: int
    telegram_id: int
    username: str
    created_at: datetime

    model_config = {"from_attributes": True}


class Category(BaseModel):
    id: int
    name: str
    parent_id: Optional[int]

    model_config = {"from_attributes": True}


class Product(BaseModel):
    id: int
    name: str
    price: float
    category_id: Optional[int] = None
    description: Optional[str] = None
    photo: Optional[str] = None

    model_config = {"from_attributes": True}


class CartItem(BaseModel):
    id: int
    product: Product
    quantity: int

    model_config = {"from_attributes": True}


class Cart(BaseModel):
    id: int
    client: Client
    items: List[CartItem]
    created_at: datetime

    model_config = {"from_attributes": True}


class OrderItem(BaseModel):
    id: int
    product: Optional[Product]
    quantity: int
    price: float

    model_config = {"from_attributes": True}


class Order(BaseModel):
    id: int
    client: Client
    address: str
    status: str
    items: List[OrderItem]
    created_at: datetime

    model_config = {"from_attributes": True}
