"""Routes for retrieving Model Kits."""

import calendar
import re
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query
from postgrest.exceptions import APIError
from app.db import supabase
from app.schemas import ModelKit


router = APIRouter(prefix="/api/v1/model_kits", tags=["Model Kits"])

# Embeds both child tables in one request.
MODEL_KIT_SELECT = (
    "*,"
    "model_kit_units(position,name,form,mobile_weapon_id,support_weapon_id),"
    "model_kit_reissues(position,date,note)"
)

# "jan" -> 1 ... "dec" -> 12; full names are matched by their first 3 letters.
_MONTHS = {name.lower(): number for number,
           name in enumerate(calendar.month_abbr) if name}


def _in_order(rows: list[dict] | None) -> list[dict]:
    """Sort child rows by position and drop the position column."""
    return [
        {key: value for key, value in row.items() if key != "position"}
        for row in sorted(rows or [], key=lambda r: r["position"])
    ]


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


@router.get("/", response_model=list[ModelKit])
def get_all_model_kits():
    """Retrieve all Model Kits from Supabase"""
    try:
        response = (
            supabase.table("model_kits")
            .select(MODEL_KIT_SELECT)
            .order("name")
            .execute()
        )
    except APIError as e:
        raise HTTPException(status_code=502, detail=e.message)

    return [_to_model_kit(row) for row in response.data]


@router.get("/search", response_model=list[ModelKit])
def search_model_kits(
    id: UUID | None = None,
    name: str | None = None,
    series: str | None = None,
    line: str | None = None,
    grade: str | None = None,
    scale: str | None = Query(
        None, description="Exact scale such as 1/144 (also 144 or 1:144), or Mixed"),
    manufacturer: str | None = None,
    release_date: str | None = Query(
        None, alias="releaseDate",
        description="A year or month in any common format: 2004, 2004-01, 01/2004, 01-2004, Jan 2004"),
    price: str | None = Query(
        None, description="An amount such as 2200 or ¥2,200; nearby prices also match"),
    threshold: float = Query(
        0.3, ge=0, le=1, description="Minimum match score (0-1) for each filter"),
    limit: int = Query(20, ge=1, le=100),
):
    """Fuzzy-search Model Kits. Filters are combined; results are ranked best match first."""
    filters = {
        "p_id": str(id) if id else None,
        "p_name": name,
        "p_series": series,
        "p_line": line,
        "p_grade": grade,
        "p_scale": _normalize_scale(scale) if scale else None,
        "p_manufacturer": manufacturer,
        "p_release_date": _normalize_release_date(release_date) if release_date else None,
        "p_price": _parse_price(price) if price else None,
    }
    if all(value is None for value in filters.values()):
        raise HTTPException(
            status_code=400, detail="Provide at least one search filter")

    try:
        matches = supabase.rpc(
            "search_model_kits",
            {**filters, "p_threshold": threshold, "p_limit": limit},
        ).execute().data
        if not matches:
            return []

        ids = [match["id"] for match in matches]
        rows = (
            supabase.table("model_kits")
            .select(MODEL_KIT_SELECT)
            .in_("id", ids)
            .execute()
            .data
        )
    except APIError as e:
        raise HTTPException(status_code=502, detail=e.message)

    # Keep the ranking from the search function.
    rank = {kit_id: position for position, kit_id in enumerate(ids)}
    rows.sort(key=lambda row: rank[row["id"]])
    return [_to_model_kit(row) for row in rows]
