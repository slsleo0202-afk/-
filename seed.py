from datetime import date, timedelta

from sqlalchemy.orm import Session

from app.auth import hash_password
from app.models import FridgeItem, IngredientPost, PostStatus, User


def seed_demo_data(db: Session) -> None:
    if db.query(User).count() > 0:
        return

    users = [
        User(
            email="seller@demo.com",
            hashed_password=hash_password("demo1234"),
            nickname="자취요리러",
            rating_average=4.8,
            rating_count=24,
            trade_count=31,
            latitude=37.555,
            longitude=126.923,
            display_area="마포구 서교동",
        ),
        User(
            email="buyer@demo.com",
            hashed_password=hash_password("demo1234"),
            nickname="대파찾는민지",
            rating_average=4.6,
            rating_count=12,
            trade_count=8,
            latitude=37.556,
            longitude=126.925,
            display_area="마포구 서교동",
        ),
        User(
            email="neighbor@demo.com",
            hashed_password=hash_password("demo1234"),
            nickname="옆집셰프",
            rating_average=4.9,
            rating_count=40,
            trade_count=52,
            latitude=37.554,
            longitude=126.920,
            display_area="마포구 합정동",
        ),
    ]
    db.add_all(users)
    db.commit()
    for u in users:
        db.refresh(u)

    today = date.today()
    posts = [
        IngredientPost(
            seller_id=users[0].id,
            title="대파 220g 판매",
            category="채소",
            ingredient_name="대파",
            quantity=220,
            quantity_unit="g",
            trade_type="SELL",
            price=1000,
            storage_type="REFRIGERATED",
            freshness_score=91,
            expiry_date=today + timedelta(days=5),
            recommended_use_by_date=today + timedelta(days=4),
            latitude=37.555,
            longitude=126.923,
            display_area="마포구 서교동",
            status=PostStatus.ACTIVE.value,
        ),
        IngredientPost(
            seller_id=users[0].id,
            title="양파 400g 나눔",
            category="채소",
            ingredient_name="양파",
            quantity=400,
            quantity_unit="g",
            trade_type="SHARE",
            price=0,
            storage_type="REFRIGERATED",
            freshness_score=84,
            expiry_date=today + timedelta(days=7),
            recommended_use_by_date=today + timedelta(days=5),
            latitude=37.555,
            longitude=126.923,
            display_area="마포구 서교동",
            status=PostStatus.ACTIVE.value,
        ),
        IngredientPost(
            seller_id=users[2].id,
            title="계란 6개 판매",
            category="유제품",
            ingredient_name="계란",
            quantity=6,
            quantity_unit="개",
            trade_type="SELL",
            price=2500,
            storage_type="REFRIGERATED",
            freshness_score=88,
            expiry_date=today + timedelta(days=10),
            recommended_use_by_date=today + timedelta(days=8),
            latitude=37.554,
            longitude=126.920,
            display_area="마포구 합정동",
            status=PostStatus.ACTIVE.value,
        ),
        IngredientPost(
            seller_id=users[2].id,
            title="대파 180g 판매",
            category="채소",
            ingredient_name="대파",
            quantity=180,
            quantity_unit="g",
            trade_type="SELL",
            price=900,
            storage_type="REFRIGERATED",
            freshness_score=88,
            expiry_date=today + timedelta(days=4),
            recommended_use_by_date=today + timedelta(days=3),
            latitude=37.554,
            longitude=126.921,
            display_area="마포구 합정동",
            status=PostStatus.ACTIVE.value,
        ),
    ]
    db.add_all(posts)

    fridge = [
        FridgeItem(
            owner_id=users[1].id,
            ingredient_name="우유",
            category="유제품",
            quantity=500,
            quantity_unit="ml",
            storage_type="REFRIGERATED",
            freshness_score=72,
            expiry_date=today + timedelta(days=2),
            recommended_use_by_date=today + timedelta(days=1),
        ),
        FridgeItem(
            owner_id=users[1].id,
            ingredient_name="당근",
            category="채소",
            quantity=200,
            quantity_unit="g",
            storage_type="REFRIGERATED",
            freshness_score=65,
            expiry_date=today + timedelta(days=5),
            recommended_use_by_date=today + timedelta(days=4),
        ),
    ]
    db.add_all(fridge)
    db.commit()
