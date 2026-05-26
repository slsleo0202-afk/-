import enum
from datetime import datetime

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class StorageType(str, enum.Enum):
    REFRIGERATED = "REFRIGERATED"
    FROZEN = "FROZEN"
    ROOM_TEMP = "ROOM_TEMP"


class TradeType(str, enum.Enum):
    SHARE = "SHARE"
    EXCHANGE = "EXCHANGE"
    SELL = "SELL"


class PostStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    RESERVED = "RESERVED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class TradeStatus(str, enum.Enum):
    REQUESTED = "REQUESTED"
    ACCEPTED = "ACCEPTED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    nickname: Mapped[str] = mapped_column(String(50))
    profile_image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    rating_average: Mapped[float] = mapped_column(Float, default=0.0)
    rating_count: Mapped[int] = mapped_column(Integer, default=0)
    trade_count: Mapped[int] = mapped_column(Integer, default=0)
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    display_area: Mapped[str | None] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    posts: Mapped[list["IngredientPost"]] = relationship(back_populates="seller")
    fridge_items: Mapped[list["FridgeItem"]] = relationship(back_populates="owner")
    trades_as_buyer: Mapped[list["Trade"]] = relationship(
        foreign_keys="Trade.buyer_id", back_populates="buyer"
    )
    trades_as_seller: Mapped[list["Trade"]] = relationship(
        foreign_keys="Trade.seller_id", back_populates="seller"
    )


class IngredientPost(Base):
    __tablename__ = "ingredient_posts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    seller_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    title: Mapped[str] = mapped_column(String(200))
    category: Mapped[str] = mapped_column(String(50))
    ingredient_name: Mapped[str] = mapped_column(String(100))
    quantity: Mapped[float] = mapped_column(Float)
    quantity_unit: Mapped[str] = mapped_column(String(10), default="g")
    trade_type: Mapped[str] = mapped_column(String(20))
    price: Mapped[int] = mapped_column(Integer, default=0)
    storage_type: Mapped[str] = mapped_column(String(20))
    freshness_score: Mapped[int] = mapped_column(Integer, default=80)
    expiry_date: Mapped[Date | None] = mapped_column(Date, nullable=True)
    recommended_use_by_date: Mapped[Date | None] = mapped_column(Date, nullable=True)
    image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    latitude: Mapped[float] = mapped_column(Float)
    longitude: Mapped[float] = mapped_column(Float)
    display_area: Mapped[str] = mapped_column(String(100))
    status: Mapped[str] = mapped_column(String(20), default=PostStatus.ACTIVE.value)
    purchase_date: Mapped[Date | None] = mapped_column(Date, nullable=True)
    has_receipt: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    seller: Mapped["User"] = relationship(back_populates="posts")
    trades: Mapped[list["Trade"]] = relationship(back_populates="post")


class FridgeItem(Base):
    __tablename__ = "fridge_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    ingredient_name: Mapped[str] = mapped_column(String(100))
    category: Mapped[str] = mapped_column(String(50))
    quantity: Mapped[float] = mapped_column(Float)
    quantity_unit: Mapped[str] = mapped_column(String(10), default="g")
    storage_type: Mapped[str] = mapped_column(String(20))
    freshness_score: Mapped[int] = mapped_column(Integer, default=80)
    expiry_date: Mapped[Date | None] = mapped_column(Date, nullable=True)
    recommended_use_by_date: Mapped[Date | None] = mapped_column(Date, nullable=True)
    purchase_date: Mapped[Date | None] = mapped_column(Date, nullable=True)
    image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    owner: Mapped["User"] = relationship(back_populates="fridge_items")


class Trade(Base):
    __tablename__ = "trades"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    post_id: Mapped[int] = mapped_column(ForeignKey("ingredient_posts.id"))
    buyer_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    seller_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    status: Mapped[str] = mapped_column(String(20), default=TradeStatus.REQUESTED.value)
    message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    post: Mapped["IngredientPost"] = relationship(back_populates="trades")
    buyer: Mapped["User"] = relationship(foreign_keys=[buyer_id], back_populates="trades_as_buyer")
    seller: Mapped["User"] = relationship(foreign_keys=[seller_id], back_populates="trades_as_seller")
    messages: Mapped[list["ChatMessage"]] = relationship(back_populates="trade")
    reviews: Mapped[list["Review"]] = relationship(back_populates="trade")


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    trade_id: Mapped[int] = mapped_column(ForeignKey("trades.id"))
    sender_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    content: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    trade: Mapped["Trade"] = relationship(back_populates="messages")


class Review(Base):
    __tablename__ = "reviews"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    trade_id: Mapped[int] = mapped_column(ForeignKey("trades.id"))
    reviewer_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    reviewee_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    rating: Mapped[int] = mapped_column(Integer)
    condition_matched: Mapped[bool] = mapped_column(Boolean, default=True)
    response_speed: Mapped[int | None] = mapped_column(Integer, nullable=True)
    trade_manner: Mapped[int | None] = mapped_column(Integer, nullable=True)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    trade: Mapped["Trade"] = relationship(back_populates="reviews")
