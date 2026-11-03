from uuid import UUID

from fastapi import APIRouter, HTTPException, Query
from postgrest.exceptions import APIError
from app.db import supabase
from app.schemas import Character


router = APIRouter(prefix="/api/v1/characters", tags=["Characters"])

# Embeds both child tables in one request.
CHARACTER_SELECT = (
    "*,"
    "character_associated_units(position,name,role,note,mobile_weapon_id,support_weapon_id),"
    "character_images(position,file,caption)"
)


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


@router.get("/", response_model=list[Character])
def get_all_characters():
    """Retrieve all Characters from Supabase"""
    try:
        response = (
            supabase.table("characters")
            .select(CHARACTER_SELECT)
            .order("name")
            .execute()
        )
    except APIError as e:
        raise HTTPException(status_code=502, detail=e.message)

    return [_to_character(row) for row in response.data]


@router.get("/search", response_model=list[Character])
def search_characters(
    id: UUID | None = None,
    name: str | None = None,
    japanese_name: str | None = Query(None, alias="japaneseName"),
    gender: str | None = None,
    birthdate: str | None = None,
    deathdate: str | None = None,
    status: str | None = None,
    affiliations: str | None = Query(
        None, description="An affiliation, matched against each of the character's affiliations"),
    rank: str | None = None,
    age: str | None = None,
    threshold: float = Query(
        0.3, ge=0, le=1, description="Minimum match score (0-1) for each filter"),
    limit: int = Query(20, ge=1, le=100),
):
    """Fuzzy-search Characters. Filters are combined; results are ranked best match first."""
    filters = {
        "p_id": str(id) if id else None,
        "p_name": name,
        "p_japanese_name": japanese_name,
        "p_gender": gender,
        "p_birthdate": birthdate,
        "p_deathdate": deathdate,
        "p_status": status,
        "p_affiliation": affiliations,
        "p_rank": rank,
        "p_age": age,
    }
    if all(value is None for value in filters.values()):
        raise HTTPException(
            status_code=400, detail="Provide at least one search filter")

    try:
        matches = supabase.rpc(
            "search_characters",
            {**filters, "p_threshold": threshold, "p_limit": limit},
        ).execute().data
        if not matches:
            return []

        ids = [match["id"] for match in matches]
        rows = (
            supabase.table("characters")
            .select(CHARACTER_SELECT)
            .in_("id", ids)
            .execute()
            .data
        )
    except APIError as e:
        raise HTTPException(status_code=502, detail=e.message)

    # Keep the ranking from the search function.
    rank_of = {character_id: position for position,
               character_id in enumerate(ids)}
    rows.sort(key=lambda row: rank_of[row["id"]])
    return [_to_character(row) for row in rows]
