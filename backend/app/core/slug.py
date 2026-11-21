import re

_TRANSLIT = {
    "а": "a", "б": "b", "в": "v", "г": "g", "д": "d", "е": "e", "ё": "e", "ж": "zh",
    "з": "z", "и": "i", "й": "y", "к": "k", "л": "l", "м": "m", "н": "n", "о": "o",
    "п": "p", "р": "r", "с": "s", "т": "t", "у": "u", "ф": "f", "х": "h", "ц": "ts",
    "ч": "ch", "ш": "sh", "щ": "sch", "ъ": "", "ы": "y", "ь": "", "э": "e", "ю": "yu",
    "я": "ya",
}  # fmt: skip


def transliterate(value: str) -> str:
    """«кнауф» → «knauf». Латиница и цифры остаются как есть."""
    return "".join(_TRANSLIT.get(char, char) for char in value.lower())


def slugify(value: str, max_length: int = 80) -> str:
    """«Штукатурка Ротбанд, 30 кг» → «shtukaturka-rotband-30-kg»."""
    text = transliterate(value)
    text = re.sub(r"[^a-z0-9]+", "-", text).strip("-")
    return text[:max_length].rstrip("-") or "item"
