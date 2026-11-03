"""Routes for retrieving Mobile Weapons."""

from uuid import UUID

from fastapi import APIRouter, HTTPException, Query
from postgrest.exceptions import APIError
from app.db import supabase
from app.schemas import MobileWeapon


router = APIRouter(prefix="/api/v1/mobile_weapons", tags=["Mobile Weapons"])

CHILD_TABLES = (
    "mobile_weapon_specs",
    "mobile_weapon_equipment",
    "mobile_weapon_armaments",
    "mobile_weapon_images",
)



# Embeds every child table in one request. Specs is 1:1 (its key is also the
# foreign key), so PostgREST returns it as an object; the rest come back as lists.
MOBILE_WEAPON_SELECT = (
    "*,"
    "mobile_weapon_specs(*),"
    "mobile_weapon_equipment(category,position,item),"
    "mobile_weapon_armaments(category,position,item),"
    "mobile_weapon_images(position,file,caption)"
)


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


@router.get("/", response_model=list[MobileWeapon])
def get_all_mobile_weapons():
    """Retrieve all Mobile Weapons from Supabase"""
    try:
        response = (
            supabase.table("mobile_weapons")
            .select(MOBILE_WEAPON_SELECT)
            .order("name")
            .execute()
        )
    except APIError as e:
        raise HTTPException(status_code=502, detail=e.message)

    return [_to_mobile_weapon(row) for row in response.data]


@router.get("/search", response_model=list[MobileWeapon])
def search_mobile_weapons(
    id: UUID | None = None,
    name: str | None = None,
    model_number: str | None = Query(None, alias="modelNumber"),
    codename: str | None = None,
    faction: str | None = None,
    era: str | None = None,
    pilots: str | None = Query(
        None, description="A pilot name, matched against each of the weapon's pilots"),
    threshold: float = Query(
        0.3, ge=0, le=1, description="Minimum match score (0-1) for each filter"),
    limit: int = Query(20, ge=1, le=100),
):
    """Fuzzy-search Mobile Weapons. Filters are combined; results are ranked best match first."""
    filters = {
        "p_id": str(id) if id else None,
        "p_name": name,
        "p_model_number": model_number,
        "p_codename": codename,
        "p_faction": faction,
        "p_era": era,
        "p_pilot": pilots,
    }
    if all(value is None for value in filters.values()):
        raise HTTPException(
            status_code=400, detail="Provide at least one search filter")

    try:
        matches = supabase.rpc(
            "search_mobile_weapons",
            {**filters, "p_threshold": threshold, "p_limit": limit},
        ).execute().data
        if not matches:
            return []

        ids = [match["id"] for match in matches]
        rows = (
            supabase.table("mobile_weapons")
            .select(MOBILE_WEAPON_SELECT)
            .in_("id", ids)
            .execute()
            .data
        )
    except APIError as e:
        raise HTTPException(status_code=502, detail=e.message)

    # Keep the ranking from the search function.
    rank = {weapon_id: position for position, weapon_id in enumerate(ids)}
    rows.sort(key=lambda row: rank[row["id"]])
    return [_to_mobile_weapon(row) for row in rows]


