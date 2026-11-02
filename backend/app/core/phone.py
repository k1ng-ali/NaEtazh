import re


def normalize_phone(value: str) -> str:
    """«8 (912) 345-67-89», «+7 912 345 67 89», «9123456789» → «+79123456789»."""
    digits = re.sub(r"\D", "", value)
    if len(digits) == 10 and digits.startswith("9"):
        digits = f"7{digits}"
    if len(digits) == 11 and digits[0] in "78":
        return f"+7{digits[1:]}"
    raise ValueError("Phone must be a Russian mobile number")
