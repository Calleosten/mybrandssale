from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List


class ProductOut(BaseModel):
    id: int
    name: str
    url: str
    image_url: Optional[str] = None
    current_price: Optional[float] = None
    original_price: Optional[float] = None
    lowest_price_seen: Optional[float] = None
    is_on_sale: bool
    brand_name: Optional[str] = None

    class Config:
        from_attributes = True


class PriceHistoryOut(BaseModel):
    price: float
    checked_at: datetime

    class Config:
        from_attributes = True


class WatchlistCreate(BaseModel):
    user_id: str
    product_id: int
    notify_threshold_percent: float = 15.0


class WatchlistOut(BaseModel):
    id: int
    product: ProductOut
    notify_threshold_percent: float

    class Config:
        from_attributes = True


class DeviceTokenCreate(BaseModel):
    user_id: str
    fcm_token: str
