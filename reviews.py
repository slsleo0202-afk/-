from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.models import Review, Trade, TradeStatus, User
from app.schemas import ReviewCreate, ReviewResponse

router = APIRouter(prefix="/api/reviews", tags=["reviews"])


@router.post("", response_model=ReviewResponse)
def create_review(
    data: ReviewCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    trade = db.query(Trade).filter(Trade.id == data.trade_id).first()
    if not trade or trade.status != TradeStatus.COMPLETED.value:
        raise HTTPException(status_code=400, detail="완료된 거래에만 후기를 남길 수 있습니다.")
    if current_user.id not in (trade.buyer_id, trade.seller_id):
        raise HTTPException(status_code=403, detail="권한이 없습니다.")
    if data.reviewee_id not in (trade.buyer_id, trade.seller_id) or data.reviewee_id == current_user.id:
        raise HTTPException(status_code=400, detail="잘못된 평가 대상입니다.")

    existing = (
        db.query(Review)
        .filter(Review.trade_id == data.trade_id, Review.reviewer_id == current_user.id)
        .first()
    )
    if existing:
        raise HTTPException(status_code=400, detail="이미 후기를 작성했습니다.")

    review = Review(
        trade_id=data.trade_id,
        reviewer_id=current_user.id,
        reviewee_id=data.reviewee_id,
        rating=data.rating,
        condition_matched=data.condition_matched,
        response_speed=data.response_speed,
        trade_manner=data.trade_manner,
        comment=data.comment,
    )
    db.add(review)

    reviewee = db.query(User).filter(User.id == data.reviewee_id).first()
    if reviewee:
        total = reviewee.rating_average * reviewee.rating_count + data.rating
        reviewee.rating_count += 1
        reviewee.rating_average = round(total / reviewee.rating_count, 2)

    db.commit()
    db.refresh(review)
    return ReviewResponse(
        id=review.id,
        trade_id=review.trade_id,
        reviewer_id=review.reviewer_id,
        reviewee_id=review.reviewee_id,
        rating=review.rating,
        condition_matched=review.condition_matched,
        comment=review.comment,
        created_at=review.created_at,
        reviewer_nickname=current_user.nickname,
    )


@router.get("/user/{user_id}", response_model=list[ReviewResponse])
def user_reviews(user_id: int, db: Session = Depends(get_db)):
    reviews = db.query(Review).filter(Review.reviewee_id == user_id).order_by(Review.created_at.desc()).limit(50).all()
    result = []
    for r in reviews:
        reviewer = db.query(User).filter(User.id == r.reviewer_id).first()
        result.append(
            ReviewResponse(
                id=r.id,
                trade_id=r.trade_id,
                reviewer_id=r.reviewer_id,
                reviewee_id=r.reviewee_id,
                rating=r.rating,
                condition_matched=r.condition_matched,
                comment=r.comment,
                created_at=r.created_at,
                reviewer_nickname=reviewer.nickname if reviewer else None,
            )
        )
    return result
