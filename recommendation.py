def quantity_similarity(item_qty: float, required_qty: float | None) -> float:
    if required_qty is None or required_qty <= 0:
        return 0.5
    diff = abs(item_qty - required_qty)
    ratio = diff / max(required_qty, 1)
    return max(0.0, 1.0 - ratio)


def price_score(price: int, average_price: float | None) -> float:
    if price <= 0:
        return 1.0
    if not average_price or average_price <= 0:
        return 0.7
    ratio = price / average_price
    if ratio <= 0.5:
        return 1.0
    if ratio >= 1.5:
        return 0.2
    return max(0.2, 1.0 - (ratio - 0.5))


def calculate_recommendation_score(
    *,
    item_quantity: float,
    required_quantity: float | None,
    distance_km: float,
    freshness_score: int,
    price: int,
    average_price: float | None,
    seller_rating: float,
) -> float:
    from app.services.location import distance_score

    q = quantity_similarity(item_quantity, required_quantity)
    d = distance_score(distance_km)
    f = freshness_score / 100.0
    p = price_score(price, average_price)
    r = seller_rating / 5.0 if seller_rating > 0 else 0.5

    return q * 0.30 + d * 0.25 + f * 0.20 + p * 0.15 + r * 0.10
