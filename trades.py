from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from app.auth import get_current_user
from app.database import get_db
from app.models import ChatMessage, IngredientPost, PostStatus, Trade, TradeStatus, User
from app.schemas import ChatMessageCreate, ChatMessageResponse, TradeCreate, TradeResponse

router = APIRouter(prefix="/api/trades", tags=["trades"])


@router.post("", response_model=TradeResponse)
def create_trade(
    data: TradeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    post = db.query(IngredientPost).filter(IngredientPost.id == data.post_id).first()
    if not post or post.status != PostStatus.ACTIVE.value:
        raise HTTPException(status_code=404, detail="거래 가능한 상품이 아닙니다.")
    if post.seller_id == current_user.id:
        raise HTTPException(status_code=400, detail="본인 상품에는 거래 요청할 수 없습니다.")

    trade = Trade(
        post_id=post.id,
        buyer_id=current_user.id,
        seller_id=post.seller_id,
        message=data.message,
    )
    post.status = PostStatus.RESERVED.value
    db.add(trade)
    db.flush()
    if data.message:
        db.add(ChatMessage(trade_id=trade.id, sender_id=current_user.id, content=data.message))
    db.commit()
    db.refresh(trade)
    return TradeResponse(
        id=trade.id,
        post_id=trade.post_id,
        buyer_id=trade.buyer_id,
        seller_id=trade.seller_id,
        status=trade.status,
        message=trade.message,
        created_at=trade.created_at,
        post_title=post.title,
        ingredient_name=post.ingredient_name,
    )


@router.get("", response_model=list[TradeResponse])
def list_trades(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    trades = (
        db.query(Trade)
        .options(joinedload(Trade.post))
        .filter((Trade.buyer_id == current_user.id) | (Trade.seller_id == current_user.id))
        .order_by(Trade.created_at.desc())
        .all()
    )
    return [
        TradeResponse(
            id=t.id,
            post_id=t.post_id,
            buyer_id=t.buyer_id,
            seller_id=t.seller_id,
            status=t.status,
            message=t.message,
            created_at=t.created_at,
            post_title=t.post.title if t.post else None,
            ingredient_name=t.post.ingredient_name if t.post else None,
        )
        for t in trades
    ]


@router.post("/{trade_id}/accept", response_model=TradeResponse)
def accept_trade(
    trade_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    trade = db.query(Trade).options(joinedload(Trade.post)).filter(Trade.id == trade_id).first()
    if not trade or trade.seller_id != current_user.id:
        raise HTTPException(status_code=404, detail="거래를 찾을 수 없습니다.")
    trade.status = TradeStatus.ACCEPTED.value
    db.commit()
    return TradeResponse(
        id=trade.id,
        post_id=trade.post_id,
        buyer_id=trade.buyer_id,
        seller_id=trade.seller_id,
        status=trade.status,
        message=trade.message,
        created_at=trade.created_at,
        post_title=trade.post.title if trade.post else None,
        ingredient_name=trade.post.ingredient_name if trade.post else None,
    )


@router.post("/{trade_id}/complete", response_model=TradeResponse)
def complete_trade(
    trade_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    trade = db.query(Trade).options(joinedload(Trade.post)).filter(Trade.id == trade_id).first()
    if not trade:
        raise HTTPException(status_code=404, detail="거래를 찾을 수 없습니다.")
    if current_user.id not in (trade.buyer_id, trade.seller_id):
        raise HTTPException(status_code=403, detail="권한이 없습니다.")

    trade.status = TradeStatus.COMPLETED.value
    trade.completed_at = datetime.utcnow()
    if trade.post:
        trade.post.status = PostStatus.COMPLETED.value
    seller = db.query(User).filter(User.id == trade.seller_id).first()
    buyer = db.query(User).filter(User.id == trade.buyer_id).first()
    if seller:
        seller.trade_count += 1
    if buyer:
        buyer.trade_count += 1
    db.commit()
    return TradeResponse(
        id=trade.id,
        post_id=trade.post_id,
        buyer_id=trade.buyer_id,
        seller_id=trade.seller_id,
        status=trade.status,
        message=trade.message,
        created_at=trade.created_at,
        post_title=trade.post.title if trade.post else None,
        ingredient_name=trade.post.ingredient_name if trade.post else None,
    )


@router.get("/{trade_id}/messages", response_model=list[ChatMessageResponse])
def get_messages(
    trade_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    trade = db.query(Trade).filter(Trade.id == trade_id).first()
    if not trade or current_user.id not in (trade.buyer_id, trade.seller_id):
        raise HTTPException(status_code=404, detail="채팅을 찾을 수 없습니다.")
    messages = db.query(ChatMessage).filter(ChatMessage.trade_id == trade_id).order_by(ChatMessage.created_at).all()
    users = {current_user.id: current_user}
    result = []
    for m in messages:
        nick = None
        if m.sender_id == current_user.id:
            nick = current_user.nickname
        else:
            other = db.query(User).filter(User.id == m.sender_id).first()
            nick = other.nickname if other else "사용자"
        result.append(
            ChatMessageResponse(
                id=m.id,
                trade_id=m.trade_id,
                sender_id=m.sender_id,
                sender_nickname=nick,
                content=m.content,
                created_at=m.created_at,
            )
        )
    return result


@router.post("/{trade_id}/messages", response_model=ChatMessageResponse)
def send_message(
    trade_id: int,
    data: ChatMessageCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    trade = db.query(Trade).filter(Trade.id == trade_id).first()
    if not trade or current_user.id not in (trade.buyer_id, trade.seller_id):
        raise HTTPException(status_code=404, detail="채팅을 찾을 수 없습니다.")
    msg = ChatMessage(trade_id=trade_id, sender_id=current_user.id, content=data.content)
    db.add(msg)
    db.commit()
    db.refresh(msg)
    return ChatMessageResponse(
        id=msg.id,
        trade_id=msg.trade_id,
        sender_id=msg.sender_id,
        sender_nickname=current_user.nickname,
        content=msg.content,
        created_at=msg.created_at,
    )
