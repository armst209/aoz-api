
import re
import calendar
from fastapi import HTTPException


# "jan" -> 1 ... "dec" -> 12; full names are matched by their first 3 letters.
_MONTHS = {name.lower(): number for number,
           name in enumerate(calendar.month_abbr) if name}

def _in_order(rows: list[dict] | None) -> list[dict]:
    """Sort child rows by position and drop the position column."""
    return [
        {key: value for key, value in row.items() if key != "position"}
        for row in sorted(rows or [], key=lambda r: r["position"])
    ]


def _to_character(row: dict) -> dict:
    """Reassemble a joined Supabase row into the nested Character shape."""
    return {
        **row,
        "associated_units": _in_order(row.pop("character_associated_units")),
        "images": _in_order(row.pop("character_images")),
    }


def _group_by_category(rows: list[dict]) -> dict[str, list[str]]:
    """Turn (category, position, item) rows back into {category: [items in order]}."""
    grouped: dict[str, list[str]] = {}
    for row in sorted(rows, key=lambda r: r["position"]):
        grouped.setdefault(row["category"], []).append(row["item"])
    return grouped


def _to_mobile_weapon(row: dict) -> dict:
    """Reassemble a joined Supabase row into the nested MobileWeapon shape."""
    specs = row.pop("mobile_weapon_specs") or {}
    specs.pop("mobile_weapon_id", None)
    images = sorted(row.pop("mobile_weapon_images") or [],
                    key=lambda r: r["position"])

    return {
        **row,
        "specs": specs,
        "equipment": _group_by_category(row.pop("mobile_weapon_equipment") or []),
        "armaments": _group_by_category(row.pop("mobile_weapon_armaments") or []),
        "images": [{"file": i["file"], "caption": i["caption"]} for i in images],
    }
    

def _to_model_kit(row: dict) -> dict:
    """Reassemble a joined Supabase row into the nested ModelKit shape."""
    amount = row.pop("price_amount")
    currency = row.pop("price_currency")
    tax_included = row.pop("price_tax_included")
    return {
        **row,
        "price": None if amount is None else {
            "amount": amount, "currency": currency, "tax_included": tax_included,
        },
        "units": _in_order(row.pop("model_kit_units")),
        "reissues": _in_order(row.pop("model_kit_reissues")),
    }


def _normalize_release_date(value: str) -> str:
    """Convert a release date in any common format to "YYYY-MM" (or "YYYY").

    Accepts 2004, 2004-01, 2004/01, 01/2004, 1-2004, 2004-01-15, Jan 2004,
    January 2004 and 2004 Jan. A day, if given, is dropped because release
    dates are stored to the month.
    """
    text = value.strip().lower()

    if match := re.fullmatch(r"(\d{4})", text):
        return match[1]

    if match := re.fullmatch(r"(\d{4})[-/. ](\d{1,2})(?:[-/. ]\d{1,2})?", text):
        year, month = match[1], int(match[2])
    elif match := re.fullmatch(r"(\d{1,2})[-/. ](\d{4})", text):
        year, month = match[2], int(match[1])
    elif match := re.fullmatch(r"([a-z]{3,})\.?[\s,-]*(\d{4})", text):
        year, month = match[2], _MONTHS.get(match[1][:3], 0)
    elif match := re.fullmatch(r"(\d{4})[\s,-]*([a-z]{3,})\.?", text):
        year, month = match[1], _MONTHS.get(match[2][:3], 0)
    else:
        year, month = None, 0

    if year is None or not 1 <= month <= 12:
        raise HTTPException(
            status_code=422,
            detail=f"Unrecognized releaseDate {value!r}. "
                   "Try 2004, 2004-01, 01/2004, 01-2004 or Jan 2004.",
        )
    return f"{year}-{month:02d}"


def _normalize_scale(value: str) -> str:
    """Convert "144", "1:144" or "1 / 144" to the stored form "1/144"."""
    text = re.sub(r"\s+", "", value).replace(":", "/")
    return f"1/{text}" if text.isdigit() else text


def _parse_price(value: str) -> float:
    """Read an amount from text such as "2200", "2,200", "¥2200" or "2200 JPY"."""
    match = re.fullmatch(r"\D*?(\d[\d,]*(?:\.\d+)?)\D*", value.strip())
    amount = float(match[1].replace(",", "")) if match else 0
    if amount <= 0:
        raise HTTPException(
            status_code=422,
            detail=f"Unrecognized price {value!r}. Try 2200, 2,200 or ¥2200.",
        )
    return amount




def _one_to_one(row: dict | None) -> dict:
    """A 1:1 child row without its foreign key column."""
    return {key: value for key, value in (row or {}).items() if key != "support_weapon_id"}


def _to_support_weapon(row: dict) -> dict:
    """Reassemble a joined Supabase row into the nested SupportWeapon shape."""
    return {
        **row,
        "specs": _one_to_one(row.pop("support_weapon_specs")),
        "mobile_suit_operations": {
            **_one_to_one(row.pop("support_weapon_ms_operations")),
            "complement": _in_order(row.pop("support_weapon_complement")),
        },
        "equipment": _group_by_category(row.pop("support_weapon_equipment")),
        "armaments": _group_by_category(row.pop("support_weapon_armaments")),
        "images": _in_order(row.pop("support_weapon_images")),
    }
