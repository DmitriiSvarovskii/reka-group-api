from datetime import datetime
from pydantic import BaseModel
from typing import List


class CartBase(BaseModel):
    product_id: int
    quantity: int


class CartCreate(CartBase):
    tg_user_id: int
    shop_id: int

    class Config:
        from_attributes = True


class CartItem(BaseModel):
    id: int
    name: str
    description: str
    quantity: int
    unit_price: float