import re

# Цифры, пробелы, скобки и дефисы, можно с плюсом в начале: «+7 (3452) 50-50-50», «8 800 555-35-35»
_DISPLAY_PHONE_RE = re.compile(r"^\+?[\d\s()\-]+$")


def clean_display_phone(value: str | None) -> str | None:
    """
    Телефон магазина так, как его покажем покупателю. Городской и 8-800 тоже подходят.

    Пусто — None. Неверный номер — ValueError.
    """
    value = " ".join((value or "").split())
    if not value:
        return None
    digits = re.sub(r"\D", "", value)
    if not _DISPLAY_PHONE_RE.match(value) or not 10 <= len(digits) <= 12:
        raise ValueError("Phone must contain 10 to 12 digits")
    return value


def normalize_phone(value: str) -> str:
    """«8 (912) 345-67-89», «+7 912 345 67 89», «9123456789» → «+79123456789»."""
    digits = re.sub(r"\D", "", value)
    if len(digits) == 10 and digits.startswith("9"):
        digits = f"7{digits}"
    if len(digits) == 11 and digits[0] in "78":
        return f"+7{digits[1:]}"
    raise ValueError("Phone must be a Russian mobile number")
