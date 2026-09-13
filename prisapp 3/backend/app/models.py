from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base


class Brand(Base):
    __tablename__ = "brands"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    base_url = Column(String, nullable=False)

    products = relationship("Product", back_populates="brand")


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    brand_id = Column(Integer, ForeignKey("brands.id"), nullable=False)
    name = Column(String, nullable=False)
    url = Column(String, nullable=False, unique=True)
    image_url = Column(String, nullable=True)
    current_price = Column(Float, nullable=True)
    original_price = Column(Float, nullable=True)
    lowest_price_seen = Column(Float, nullable=True)
    last_checked = Column(DateTime, default=datetime.utcnow)
    is_on_sale = Column(Boolean, default=False)

    brand = relationship("Brand", back_populates="products")
    price_history = relationship("PriceHistory", back_populates="product")


class PriceHistory(Base):
    __tablename__ = "price_history"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    price = Column(Float, nullable=False)
    checked_at = Column(DateTime, default=datetime.utcnow)

    product = relationship("Product", back_populates="price_history")


class WatchlistItem(Base):
    """Vilka produkter/märken en användare bevakar. user_id är en enkel sträng
    (t.ex. ett device-ID) eftersom appen inte har inloggning i detta skelett."""
    __tablename__ = "watchlist_items"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True, nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    notify_threshold_percent = Column(Float, default=15.0)  # notifiera vid t.ex. 15% rabatt

    product = relationship("Product")


class DeviceToken(Base):
    """FCM push-token per device, kopplat till samma user_id som watchlist."""
    __tablename__ = "device_tokens"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True, nullable=False)
    fcm_token = Column(String, unique=True, nullable=False)
