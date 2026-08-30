import re
from decimal import Decimal, InvalidOperation


def normalize_header(header: str) -> str:
    """Lowercase, strip spaces/underscores for fuzzy column matching."""
    return re.sub(r"[\s_\-]+", "", header.strip().lower())


COLUMN_ALIASES: dict[str, list[str]] = {
    "price": ["price", "cost", "amount", "mrp", "sellingprice", "selling_price"],
    "title": ["title", "name", "productname", "product_name", "item"],
    "sku": ["sku", "productid", "product_id", "id", "itemcode", "item_code"],
    "stock": ["stock", "quantity", "qty", "inventory"],
    "description": ["description", "desc", "details", "productdescription"],
    "category": ["category", "cat", "type", "productcategory"],
    "image_url": ["imageurl", "image_url", "image", "img", "photo"],
}


def build_column_map(headers: list[str]) -> dict[str, str | None]:
    """Map canonical field names to actual CSV column names."""
    normalized_headers = {normalize_header(h): h for h in headers}
    result: dict[str, str | None] = {field: None for field in COLUMN_ALIASES}

    for field, aliases in COLUMN_ALIASES.items():
        for alias in aliases:
            normalized_alias = normalize_header(alias)
            if normalized_alias in normalized_headers:
                result[field] = normalized_headers[normalized_alias]
                break

    return result


def parse_price(value: object) -> Decimal | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text or text.lower() in {"nan", "none", "null"}:
        return None
    cleaned = re.sub(r"[₹,\s]", "", text)
    try:
        amount = Decimal(cleaned)
        if amount < 0:
            return None
        return amount.quantize(Decimal("0.01"))
    except (InvalidOperation, ValueError):
        return None


def parse_int(value: object, default: int = 0) -> int:
    if value is None:
        return default
    text = str(value).strip()
    if not text or text.lower() in {"nan", "none", "null"}:
        return default
    try:
        return int(float(text))
    except (ValueError, TypeError):
        return default


def parse_str(value: object, default: str = "") -> str:
    if value is None:
        return default
    text = str(value).strip()
    if text.lower() in {"nan", "none", "null"}:
        return default
    return text
