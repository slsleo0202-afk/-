from datetime import date, timedelta

STORAGE_DAYS = {
    "REFRIGERATED": 7,
    "FROZEN": 30,
    "ROOM_TEMP": 3,
}

CATEGORY_DEFAULTS = {
    "채소": ("REFRIGERATED", 7),
    "과일": ("REFRIGERATED", 5),
    "육류": ("REFRIGERATED", 3),
    "수산물": ("REFRIGERATED", 2),
    "유제품": ("REFRIGERATED", 7),
    "곡물·면류": ("ROOM_TEMP", 180),
    "양념·소스": ("ROOM_TEMP", 365),
    "가공식품": ("ROOM_TEMP", 90),
}


def freshness_label(score: int) -> str:
    if score >= 90:
        return "매우 신선"
    if score >= 70:
        return "신선"
    if score >= 50:
        return "보통"
    if score >= 30:
        return "주의"
    return "위험"


def calculate_freshness_score(
    *,
    days_since_purchase: int = 0,
    days_until_expiry: int | None = None,
    storage_type: str = "REFRIGERATED",
    has_receipt: bool = False,
    image_risk_level: int = 0,
) -> int:
    score = 100.0
    score -= days_since_purchase * 3
    score -= image_risk_level * 10

    if days_until_expiry is not None:
        if days_until_expiry <= 0:
            score -= 40
        elif days_until_expiry <= 1:
            score -= 30
        elif days_until_expiry <= 3:
            score -= 15
        elif days_until_expiry <= 7:
            score -= 5

    if storage_type == "FROZEN":
        score += 10
    elif storage_type == "ROOM_TEMP":
        score -= 10

    if has_receipt:
        score += 5

    return max(0, min(100, int(round(score))))


def predict_use_by_date(
    purchase_date: date | None,
    expiry_date: date | None,
    storage_type: str,
    category: str = "채소",
) -> date | None:
    if expiry_date:
        return expiry_date - timedelta(days=1)
    base = purchase_date or date.today()
    days = STORAGE_DAYS.get(storage_type, CATEGORY_DEFAULTS.get(category, ("REFRIGERATED", 7))[1])
    return base + timedelta(days=days)


def days_between(start: date, end: date) -> int:
    return (end - start).days


def build_warnings(score: int, days_until_expiry: int | None) -> list[str]:
    warnings: list[str] = []
    if score < 30:
        warnings.append("신선도가 매우 낮습니다. 거래 제한 또는 나눔 전용을 권장합니다.")
    elif score < 50:
        warnings.append("빠른 소비가 필요합니다.")
    if days_until_expiry is not None and days_until_expiry <= 0:
        warnings.append("유통기한이 지났습니다. 거래 등록을 권장하지 않습니다.")
    return warnings
