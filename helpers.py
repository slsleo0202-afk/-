from datetime import date

from app.models import IngredientPost, User
from app.schemas import IngredientResponse
from app.services.freshness import freshness_label
from app.services.location import haversine_km
from app.services.recommendation import calculate_recommendation_score


def post_to_response(
    post: IngredientPost,
    *,
    user_lat: float | None = None,
    user_lng: float | None = None,
    required_quantity: float | None = None,
    average_price: float | None = None,
) -> IngredientResponse:
    distance_km = None
    recommendation_score = None
    if user_lat is not None and user_lng is not None:
        distance_km = haversine_km(user_lat, user_lng, post.latitude, post.longitude)
        seller_rating = post.seller.rating_average if post.seller else 0.0
        recommendation_score = calculate_recommendation_score(
            item_quantity=post.quantity,
            required_quantity=required_quantity,
            distance_km=distance_km,
            freshness_score=post.freshness_score,
            price=post.price,
            average_price=average_price,
            seller_rating=seller_rating,
        )

    return IngredientResponse(
        id=post.id,
        seller_id=post.seller_id,
        title=post.title,
        category=post.category,
        ingredient_name=post.ingredient_name,
        quantity=post.quantity,
        quantity_unit=post.quantity_unit,
        trade_type=post.trade_type,
        price=post.price,
        storage_type=post.storage_type,
        freshness_score=post.freshness_score,
        freshness_label=freshness_label(post.freshness_score),
        expiry_date=post.expiry_date,
        recommended_use_by_date=post.recommended_use_by_date,
        image_url=post.image_url,
        latitude=post.latitude,
        longitude=post.longitude,
        display_area=post.display_area,
        status=post.status,
        distance_km=round(distance_km, 2) if distance_km is not None else None,
        recommendation_score=round(recommendation_score, 4) if recommendation_score else None,
        seller_nickname=post.seller.nickname if post.seller else None,
        seller_rating=post.seller.rating_average if post.seller else None,
        created_at=post.created_at,
    )


def compute_freshness_inputs(
    purchase_date: date | None,
    expiry_date: date | None,
    storage_type: str,
    has_receipt: bool,
    image_risk_level: int,
) -> tuple[int, int | None]:
    today = date.today()
    days_since = 0
    if purchase_date:
        days_since = max(0, (today - purchase_date).days)
    days_until = None
    if expiry_date:
        days_until = (expiry_date - today).days
    return days_since, days_until


def trade_type_label(trade_type: str) -> str:
    return {"SHARE": "나눔", "EXCHANGE": "교환", "SELL": "판매"}.get(trade_type, trade_type)


def build_title(name: str, qty: float, unit: str, trade_type: str) -> str:
    label = trade_type_label(trade_type)
    return f"{name} {qty:g}{unit} {label}"
