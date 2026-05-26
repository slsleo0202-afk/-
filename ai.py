from datetime import date

from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.helpers import compute_freshness_inputs
from app.models import User
from app.schemas import ClassifyRequest, ClassifyResponse, FreshnessRequest, FreshnessResponse
from app.services.ai_classifier import classify_from_filename, classify_from_hint
from app.services.freshness import (
    build_warnings,
    calculate_freshness_score,
    freshness_label,
    predict_use_by_date,
)

router = APIRouter(prefix="/api/ai", tags=["ai"])


@router.post("/freshness", response_model=FreshnessResponse)
def analyze_freshness(
    body: FreshnessRequest,
    current_user: User = Depends(get_current_user),
):
    name = body.ingredient_name or "식재료"
    category = body.category or "채소"
    days_since, days_until = compute_freshness_inputs(
        body.purchase_date, body.expiry_date, body.storage_type, body.has_receipt, body.image_risk_level
    )
    score = calculate_freshness_score(
        days_since_purchase=days_since,
        days_until_expiry=days_until,
        storage_type=body.storage_type,
        has_receipt=body.has_receipt,
        image_risk_level=body.image_risk_level,
    )
    use_by = predict_use_by_date(body.purchase_date, body.expiry_date, body.storage_type, category)
    warnings = build_warnings(score, days_until)
    confidence = 0.87 if body.has_receipt else 0.72
    return FreshnessResponse(
        ingredient_name=name,
        category=category,
        freshness_score=score,
        freshness_label=freshness_label(score),
        recommended_use_by_date=use_by,
        confidence=confidence,
        warnings=warnings,
    )


@router.post("/classify", response_model=ClassifyResponse)
async def classify_ingredient_json(
    body: ClassifyRequest,
    current_user: User = Depends(get_current_user),
):
    hint = body.hint
    if hint:
        name, category, qty, conf = classify_from_hint(hint)
    else:
        name, category, qty, conf = classify_from_hint(None)
    return ClassifyResponse(
        ingredient_name=name,
        category=category,
        estimated_quantity=qty,
        quantity_unit="g",
        confidence=conf,
    )


@router.post("/classify-form", response_model=ClassifyResponse)
async def classify_ingredient(
    hint: str | None = Form(None),
    image: UploadFile | None = File(None),
    current_user: User = Depends(get_current_user),
):
    if hint:
        name, category, qty, conf = classify_from_hint(hint)
    elif image and image.filename:
        name, category, qty, conf = classify_from_filename(image.filename)
    else:
        name, category, qty, conf = classify_from_hint(None)
    return ClassifyResponse(
        ingredient_name=name,
        category=category,
        estimated_quantity=qty,
        quantity_unit="g",
        confidence=conf,
    )


@router.post("/classify-image", response_model=ClassifyResponse)
async def classify_image(
    image: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
):
    name, category, qty, conf = classify_from_filename(image.filename)
    return ClassifyResponse(
        ingredient_name=name,
        category=category,
        estimated_quantity=qty,
        quantity_unit="g",
        confidence=conf,
    )
