from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, EmailStr, Field


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)
    nickname: str = Field(min_length=2, max_length=50)
    latitude: float | None = None
    longitude: float | None = None
    display_area: str | None = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: int
    email: str
    nickname: str
    profile_image_url: str | None
    rating_average: float
    rating_count: int
    trade_count: int
    display_area: str | None
    latitude: float | None
    longitude: float | None
    created_at: datetime

    model_config = {"from_attributes": True}


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class LocationInput(BaseModel):
    latitude: float
    longitude: float
    display_area: str | None = None


class IngredientCreate(BaseModel):
    ingredient_name: str
    category: str
    quantity: float
    quantity_unit: str = "g"
    trade_type: Literal["SHARE", "EXCHANGE", "SELL"]
    price: int = 0
    storage_type: Literal["REFRIGERATED", "FROZEN", "ROOM_TEMP"]
    expiry_date: date | None = None
    purchase_date: date | None = None
    location: LocationInput
    title: str | None = None
    has_receipt: bool = False
    image_risk_level: int = 0
    register_to_fridge: bool = False


class IngredientResponse(BaseModel):
    id: int
    seller_id: int
    title: str
    category: str
    ingredient_name: str
    quantity: float
    quantity_unit: str
    trade_type: str
    price: int
    storage_type: str
    freshness_score: int
    freshness_label: str
    expiry_date: date | None
    recommended_use_by_date: date | None
    image_url: str | None
    latitude: float
    longitude: float
    display_area: str
    status: str
    distance_km: float | None = None
    recommendation_score: float | None = None
    seller_nickname: str | None = None
    seller_rating: float | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class FreshnessRequest(BaseModel):
    ingredient_name: str | None = None
    category: str | None = None
    storage_type: Literal["REFRIGERATED", "FROZEN", "ROOM_TEMP"] = "REFRIGERATED"
    purchase_date: date | None = None
    expiry_date: date | None = None
    has_receipt: bool = False
    image_risk_level: int = 0


class FreshnessResponse(BaseModel):
    ingredient_name: str
    category: str
    freshness_score: int
    freshness_label: str
    recommended_use_by_date: date | None
    confidence: float
    warnings: list[str]


class ClassifyRequest(BaseModel):
    hint: str | None = None


class ClassifyResponse(BaseModel):
    ingredient_name: str
    category: str
    estimated_quantity: float
    quantity_unit: str
    confidence: float


class TradeCreate(BaseModel):
    post_id: int
    message: str | None = None


class TradeResponse(BaseModel):
    id: int
    post_id: int
    buyer_id: int
    seller_id: int
    status: str
    message: str | None
    created_at: datetime
    post_title: str | None = None
    ingredient_name: str | None = None

    model_config = {"from_attributes": True}


class ChatMessageCreate(BaseModel):
    content: str


class ChatMessageResponse(BaseModel):
    id: int
    trade_id: int
    sender_id: int
    sender_nickname: str | None = None
    content: str
    created_at: datetime

    model_config = {"from_attributes": True}


class ReviewCreate(BaseModel):
    trade_id: int
    reviewee_id: int
    rating: int = Field(ge=1, le=5)
    condition_matched: bool = True
    response_speed: int | None = Field(default=None, ge=1, le=5)
    trade_manner: int | None = Field(default=None, ge=1, le=5)
    comment: str | None = None


class ReviewResponse(BaseModel):
    id: int
    trade_id: int
    reviewer_id: int
    reviewee_id: int
    rating: int
    condition_matched: bool
    comment: str | None
    created_at: datetime
    reviewer_nickname: str | None = None

    model_config = {"from_attributes": True}


class FridgeItemCreate(BaseModel):
    ingredient_name: str
    category: str
    quantity: float
    quantity_unit: str = "g"
    storage_type: Literal["REFRIGERATED", "FROZEN", "ROOM_TEMP"]
    expiry_date: date | None = None
    purchase_date: date | None = None
    has_receipt: bool = False


class FridgeItemResponse(BaseModel):
    id: int
    ingredient_name: str
    category: str
    quantity: float
    quantity_unit: str
    storage_type: str
    freshness_score: int
    freshness_label: str
    expiry_date: date | None
    recommended_use_by_date: date | None
    days_until_expiry: int | None
    image_url: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class HomeResponse(BaseModel):
    expiring_soon: list[FridgeItemResponse]
    nearby_posts: list[IngredientResponse]
    recommended_posts: list[IngredientResponse]
