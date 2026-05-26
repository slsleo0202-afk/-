from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.helpers import compute_freshness_inputs
from app.models import FridgeItem, User
from app.schemas import FridgeItemCreate, FridgeItemResponse
from app.services.freshness import calculate_freshness_score, freshness_label, predict_use_by_date

router = APIRouter(prefix="/api/fridge", tags=["fridge"])


@router.get("", response_model=list[FridgeItemResponse])
def list_fridge(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    today = date.today()
    items = db.query(FridgeItem).filter(FridgeItem.owner_id == current_user.id).all()
    result = []
    for item in items:
        days = None
        if item.recommended_use_by_date:
            days = (item.recommended_use_by_date - today).days
        result.append(
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
    result.sort(key=lambda x: (x.days_until_expiry is None, x.days_until_expiry or 999))
    return result


@router.post("", response_model=FridgeItemResponse)
def add_fridge_item(
    data: FridgeItemCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    days_since, days_until = compute_freshness_inputs(
        data.purchase_date, data.expiry_date, data.storage_type, data.has_receipt, 0
    )
    score = calculate_freshness_score(
        days_since_purchase=days_since,
        days_until_expiry=days_until,
        storage_type=data.storage_type,
        has_receipt=data.has_receipt,
    )
    use_by = predict_use_by_date(data.purchase_date, data.expiry_date, data.storage_type, data.category)
    item = FridgeItem(
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
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    days = (use_by - date.today()).days if use_by else None
    return FridgeItemResponse(
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


@router.delete("/{item_id}")
def delete_fridge_item(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    item = db.query(FridgeItem).filter(FridgeItem.id == item_id, FridgeItem.owner_id == current_user.id).first()
    if not item:
        raise HTTPException(status_code=404, detail="항목을 찾을 수 없습니다.")
    db.delete(item)
    db.commit()
    return {"ok": True}
