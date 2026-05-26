import math


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlon / 2) ** 2
    return r * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def format_distance(km: float) -> str:
    if km < 1:
        return f"{int(km * 1000)}m"
    return f"{km:.1f}km"


def distance_score(km: float, max_km: float = 5.0) -> float:
    if km <= 0:
        return 1.0
    if km >= max_km:
        return 0.0
    return 1.0 - (km / max_km)
