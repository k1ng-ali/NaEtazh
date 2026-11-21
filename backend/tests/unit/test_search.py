from sqlalchemy.dialects import postgresql

from app.core.search import latin_variant, normalize, search_terms
from app.repositories.catalog_repo import search_conditions


def compile_sql(clause) -> str:
    return str(clause.compile(dialect=postgresql.dialect(), compile_kwargs={"literal_binds": True}))


def test_normalize_matches_search_text_column():
    # Как translate(lower(...), 'ёx', 'ех') в products.search_text
    assert normalize("Шпаклёвка 30x3") == "шпаклевка 30х3"


def test_search_terms_split_words_and_drop_repeats():
    assert search_terms("  Ротбанд, Кнауф  ротбанд 30кг!") == ["ротбанд", "кнауф", "30кг"]


def test_search_terms_without_words_are_empty():
    assert search_terms("!!! ...") == []


def test_search_terms_are_limited():
    assert len(search_terms(" ".join(f"слово{i}" for i in range(20)))) == 8


def test_latin_variant_only_for_cyrillic():
    assert latin_variant("кнауф") == "knauf"
    assert latin_variant("knauf") is None
    assert latin_variant("30") is None


def test_empty_query_finds_nothing():
    matches, order = search_conditions("!!!")
    assert compile_sql(matches) == "false"
    assert order == []


def test_short_word_is_only_substring():
    matches, _ = search_conditions("м2")
    sql = compile_sql(matches)
    assert "LIKE" in sql
    assert "plainto_tsquery" not in sql
    assert "<%%" not in sql


def test_long_word_uses_forms_typos_and_latin():
    matches, order = search_conditions("Ротбнд")
    sql = compile_sql(matches)
    assert "LIKE '%%' || 'ротбнд' || '%%'" in sql
    assert "plainto_tsquery('russian'::regconfig, 'ротбнд')" in sql
    assert "'ротбнд' <%% products.search_text" in sql
    assert "LIKE '%%' || 'rotbnd' || '%%'" in sql
    assert len(order) == 2


def test_every_word_must_match():
    matches, _ = search_conditions("клей плитки")
    sql = compile_sql(matches)
    assert sql.count(" AND ") >= 1
    assert "клей" in sql and "плитки" in sql
