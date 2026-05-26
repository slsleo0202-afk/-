import uuid
from datetime import date
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.auth import get_current_user, get_optional_user
from app.config import settings
from app.database import get_db
from app.helpers import build_title, compute_freshness_inputs, post_to_response
from app.models import FridgeItem, IngredientPost, PostStatus, User
from app.schemas import HomeResponse, IngredientCreate, IngredientResponse
from app.services.freshness import calculate_freshness_score, predict_use_by_date
from app.services.freshness import freshness_label
from app.schemas import FridgeItemResponse

router = APIRouter(prefix="/api", tags=["ingredients"])


def _save_image(file: UploadFile | None) -> str | None:
    if not file or not file.filename:
        return None
    ext = Path(file.filename).suffix or ".jpg"
    name = f"{uuid.uuid4().hex}{ext}"
    path = settings.upload_dir / name
    content = file.file.read()
    path.write_bytes(content)
    return f"/uploads/{name}"


@router.post("/ingredients", response_model=IngredientResponse)
async def create_ingredient(
    data: IngredientCreate,
    image: UploadFile | None = File(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    days_since, days_until = compute_freshness_inputs(
        data.purchase_date, data.expiry_date, data.storage_type, data.has_receipt, data.image_risk_level
    )
    score = calculate_freshness_score(
        days_since_purchase=days_since,
        days_until_expiry=days_until,
        storage_type=data.storage_type,
        has_receipt=data.has_receipt,
        image_risk_level=data.image_risk_level,
    )
    if score < 30:
        raise HTTPException(status_code=400, detail="신선도가 너무 낮아 거래 등록이 제한됩니다.")

    use_by = predict_use_by_date(data.purchase_date, data.expiry_date, data.storage_type, data.category)
    image_url = _save_image(image)
    title = data.title or build_title(data.ingredient_name, data.quantity, data.quantity_unit, data.trade_type)
    display_area = data.location.display_area or current_user.display_area or "근처"

    post = IngredientPost(
        seller_id=current_user.id,
        title=title,
        category=data.category,
        ingredient_name=data.ingredient_name,
        quantity=data.quantity,
        quantity_unit=data.quantity_unit,
        trade_type=data.trade_type,
        price=data.price if data.trade_type == "SELL" else 0,
        storage_type=data.storage_type,
        freshness_score=score,
        expiry_date=data.expiry_date,
        recommended_use_by_date=use_by,
        image_url=image_url,
        latitude=data.location.latitude,
        longitude=data.location.longitude,
        display_area=display_area,
        purchase_date=data.purchase_date,
        has_receipt=data.has_receipt,
    )
    db.add(post)

    if data.register_to_fridge:
        fridge = FridgeItem(
            owner_id=current_user.id,
            ingredient_name=data.ingredient_name,
            category=data.category,
            quantity=data.quantity,
            quantity_unit=data.quantity_unit,
            storage_type=data.storage_type,
            freshness_score=score,
            expiry_date=data.expiry_date,
            recommended_use_by_date=use_by,
            purchase_date=data.purchase_date,
            image_url=image_url,
        )
        db.add(fridge)

    db.commit()
    db.refresh(post)
    post = db.query(IngredientPost).options(joinedload(IngredientPost.seller)).filter(IngredientPost.id == post.id).first()
    return post_to_response(post, user_lat=data.location.latitude, user_lng=data.location.longitude)


@router.get("/ingredients", response_model=list[IngredientResponse])
def search_ingredients(
    keyword: str | None = None,
    sort: str = Query("recommend", pattern="^(recommend|distance|freshness|price|quantity)$"),
    required_quantity: float | None = None,
    unit: str = "g",
    lat: float | None = None,
    lng: float | None = None,
    radius_km: float = Query(5.0, le=20.0),
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_optional_user),
):
    q = (
        db.query(IngredientPost)
        .options(joinedload(IngredientPost.seller))
        .filter(IngredientPost.status == PostStatus.ACTIVE.value)
    )
    if keyword:
        q = q.filter(
            IngredientPost.ingredient_name.contains(keyword) | IngredientPost.title.contains(keyword)
        )

    posts = q.all()
    user_lat = lat or (current_user.latitude if current_user else 37.555)
    user_lng = lng or (current_user.longitude if current_user else 126.923)

    avg_price_row = db.query(func.avg(IngredientPost.price)).filter(IngredientPost.price > 0).scalar()
    average_price = float(avg_price_row) if avg_price_row else None

    results: list[IngredientResponse] = []
    for post in posts:
        resp = post_to_response(
            post,
            user_lat=user_lat,
            user_lng=user_lng,
            required_quantity=required_quantity,
            average_price=average_price,
        )
        if resp.distance_km is not None and resp.distance_km > radius_km:
            continue
        results.append(resp)

    if sort == "distance":
        results.sort(key=lambda x: x.distance_km or 999)
    elif sort == "freshness":
        results.sort(key=lambda x: x.freshness_score, reverse=True)
    elif sort == "price":
        results.sort(key=lambda x: x.price)
    elif sort == "quantity":
        results.sort(key=lambda x: x.quantity, reverse=True)
    else:
        results.sort(key=lambda x: x.recommendation_score or 0, reverse=True)

    return results


@router.get("/ingredients/{post_id}", response_model=IngredientResponse)
def get_ingredient(
    post_id: int,
    lat: float | None = None,
    lng: float | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    post = (
        db.query(IngredientPost)
        .options(joinedload(IngredientPost.seller))
        .filter(IngredientPost.id == post_id)
        .first()
    )
    if not post:
        raise HTTPException(status_code=404, detail="상품을 찾을 수 없습니다.")
    user_lat = lat or current_user.latitude or 37.555
    user_lng = lng or current_user.longitude or 126.923
    return post_to_response(post, user_lat=user_lat, user_lng=user_lng)


@router.get("/home", response_model=HomeResponse)
def home(
    lat: float | None = None,
    lng: float | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    user_lat = lat or current_user.latitude or 37.555
    user_lng = lng or current_user.longitude or 126.923
    today = date.today()

    fridge_rows = db.query(FridgeItem).filter(FridgeItem.owner_id == current_user.id).all()
    expiring: list[FridgeItemResponse] = []
    for item in fridge_rows:
        days = None
        if item.recommended_use_by_date:
            days = (item.recommended_use_by_date - today).days
        if days is not None and days <= 3:
            expiring.append(
                FridgeItemResponse(
                    id=item.id,
                    ingredient_name=item.ingredient_name,
                    category=item.category,
                    quantity=item.quantity,
                    quantity_unit=item.quantity_unit,
                    storage_type=item.storage_type,
                    freshness_score=item.freshness_score,
                    freshness_label=freshness_label(item.freshness_score),
                    expiry_date=item.expiry_date,
                    recommended_use_by_date=item.recommended_use_by_date,
                    days_until_expiry=days,
                    image_url=item.image_url,
                    created_at=item.created_at,
                )
            )

    posts = (
        db.query(IngredientPost)
        .options(joinedload(IngredientPost.seller))
        .filter(IngredientPost.status == PostStatus.ACTIVE.value)
        .limit(20)
        .all()
    )
    avg_price = db.query(func.avg(IngredientPost.price)).filter(IngredientPost.price > 0).scalar()
    responses = [
        post_to_response(p, user_lat=user_lat, user_lng=user_lng, average_price=float(avg_price) if avg_price else None)
        for p in posts
    ]
    responses.sort(key=lambda x: x.distance_km or 999)
    nearby = responses[:8]
    recommended = sorted(responses, key=lambda x: x.recommendation_score or 0, reverse=True)[:6]

    return HomeResponse(expiring_soon=expiring, nearby_posts=nearby, recommended_posts=recommended)
