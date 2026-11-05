
from uuid import UUID
from fastapi import APIRouter, HTTPException, Query
from postgrest.exceptions import APIError
from app.core.db import supabase
from app.schemas import SupportWeapon, SupportWeaponsOrderBy
from app.utils import _to_support_weapon


router = APIRouter(prefix="/api/v1/support_weapons", tags=["Support Weapons"])

# Embeds every child table in one request. Specs and mobile suit operations are
# 1:1 (their key is also the foreign key), so PostgREST returns them as objects;
# the rest come back as lists.
SUPPORT_WEAPON_SELECT = (
    "*,"
    "support_weapon_specs(*),"
    "support_weapon_ms_operations(*),"
    "support_weapon_complement(position,group,units),"
    "support_weapon_equipment(category,position,item),"
    "support_weapon_armaments(category,position,item),"
    "support_weapon_images(position,file,caption)"
)



@router.get("/", response_model=list[SupportWeapon])
def get_all_support_weapons(
    order_by: SupportWeaponsOrderBy = SupportWeaponsOrderBy.NAME,
    limit_by: int | None = Query(None, ge=1),
):
    """Retrieve all Support Weapons from Supabase"""
    query = (
        supabase.table("support_weapons")
        .select(SUPPORT_WEAPON_SELECT)
        .order(order_by.value, nullsfirst=False)
    )
    if order_by is not SupportWeaponsOrderBy.NAME:
        query = query.order("name")  # tie-breaker for equal or missing values
    if limit_by is not None:
        query = query.limit(limit_by)

    try:
        response = query.execute()
    except APIError as e:
        raise HTTPException(status_code=502, detail=e.message)

    return [_to_support_weapon(row) for row in response.data]


@router.get("/search", response_model=list[SupportWeapon])
def search_support_weapons(
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
    """Fuzzy-search Support Weapons. Filters are combined; results are ranked best match first."""
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
            "search_support_weapons",
            {**filters, "p_threshold": threshold, "p_limit": limit},
        ).execute().data
        if not matches:
            return []

        ids = [match["id"] for match in matches]
        rows = (
            supabase.table("support_weapons")
            .select(SUPPORT_WEAPON_SELECT)
            .in_("id", ids)
            .execute()
            .data
        )
    except APIError as e:
        raise HTTPException(status_code=502, detail=e.message)

    # Keep the ranking from the search function.
    rank = {weapon_id: position for position, weapon_id in enumerate(ids)}
    rows.sort(key=lambda row: rank[row["id"]])
    return [_to_support_weapon(row) for row in rows]
