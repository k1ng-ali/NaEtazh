"""
Поиск товаров на витрине.

В базе у товара есть search_text: название и бренд в нижнем регистре, «ё» заменена на «е»,
латинская «x» на русскую «х», чтобы «30x3» находило «30х3мм». Запрос нормализуется так же.
"""

import re

from app.core.slug import transliterate

# То же преобразование, что в колонке products.search_text: translate(lower(...), 'ёx', 'ех')
_NORMALIZE = str.maketrans("ёx", "ех")
_WORD_RE = re.compile(r"\w+")
_CYRILLIC_RE = re.compile(r"[а-я]")

MAX_TERMS = 8
# Словоформы ищем у слов от 3 букв, опечатки — от 5: в коротком слове одна буква меняет
# почти все триграммы, и «клей» начинает находить «клеммы»
MIN_STEM_LENGTH = 3
MIN_FUZZY_LENGTH = 5
# Порог word_similarity на время поиска. По умолчанию в pg_trgm 0.6, и «ротбнд» (0.57)
# не находит «Ротбанд», а «плитки» — «плиточный»
WORD_SIMILARITY_THRESHOLD = 0.5


def normalize(value: str) -> str:
    return value.lower().translate(_NORMALIZE)


def search_terms(query: str) -> list[str]:
    """«Ротбанд  Кнауф, 30кг» → ["ротбанд", "кнауф", "30кг"]. Повторы убираются."""
    terms = _WORD_RE.findall(normalize(query))
    return list(dict.fromkeys(terms))[:MAX_TERMS]


def latin_variant(term: str) -> str | None:
    """Бренды в названиях часто латиницей: «кнауф» → «knauf». Без кириллицы вариант не нужен."""
    if not _CYRILLIC_RE.search(term):
        return None
    return transliterate(term)
