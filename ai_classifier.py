"""규칙 기반 식재료 분류 (추후 OCR/이미지 모델로 교체 가능)."""

KEYWORD_MAP = {
    "양파": ("양파", "채소", 400),
    "대파": ("대파", "채소", 200),
    "파": ("대파", "채소", 150),
    "당근": ("당근", "채소", 300),
    "감자": ("감자", "채소", 500),
    "상추": ("상추", "채소", 150),
    "사과": ("사과", "과일", 300),
    "바나나": ("바나나", "과일", 250),
    "귤": ("귤", "과일", 500),
    "계란": ("계란", "유제품", 300),
    "우유": ("우유", "유제품", 1000),
    "닭": ("닭가슴살", "육류", 300),
    "돼지": ("돼지고기", "육류", 300),
    "소고기": ("소고기", "육류", 300),
    "생선": ("생선", "수산물", 300),
    "라면": ("라면", "곡물·면류", 120),
    "쌀": ("쌀", "곡물·면류", 1000),
}

DEFAULT = ("식재료", "채소", 200)


def classify_from_hint(hint: str | None = None) -> tuple[str, str, float, float]:
    if not hint:
        return (*DEFAULT, 0.55)
    lower = hint.lower()
    for key, (name, cat, qty) in KEYWORD_MAP.items():
        if key in lower or key in hint:
            return name, cat, float(qty), 0.82
    return (*DEFAULT, 0.6)


def classify_from_filename(filename: str | None) -> tuple[str, str, float, float]:
    if not filename:
        return classify_from_hint(None)
    stem = filename.rsplit(".", 1)[0].replace("_", " ").replace("-", " ")
    return classify_from_hint(stem)
