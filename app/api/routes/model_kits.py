
from uuid import UUID
from fastapi import APIRouter, HTTPException, Query
from postgrest.exceptions import APIError
from app.core.db import supabase
from app.schemas import ModelKit, ModelKitsOrderBy
from app.utils import _to_model_kit,_normalize_scale, _normalize_release_date, _parse_price


router = APIRouter(prefix="/api/v1/model_kits", tags=["Model Kits"])

# Embeds both child tables in one request.
MODEL_KIT_SELECT = (
    "*,"
    "model_kit_units(position,name,form,mobile_weapon_id,support_weapon_id),"
    "model_kit_reissues(position,date,note)"
)


# scale and grade are text that sorts wrongly ("1/60" after "1/400", Perfect
# Grade before Real Grade), so they sort by the generated columns from the
# model_kits_sort_columns migration instead.
SORT_COLUMNS = {
    ModelKitsOrderBy.NAME: "name",
    ModelKitsOrderBy.SCALE: "scale_sort",
    ModelKitsOrderBy.GRADE: "grade_sort",
}


@router.get("/", response_model=list[ModelKit])
def get_all_model_kits(
    order_by: ModelKitsOrderBy = ModelKitsOrderBy.NAME,
    limit_by: int | None = Query(None, ge=1),
):
    """Retrieve all Model Kits from Supabase"""
    query = (
        supabase.table("model_kits")
        .select(MODEL_KIT_SELECT)
        .order(SORT_COLUMNS[order_by], nullsfirst=False)
    )
    if order_by is not ModelKitsOrderBy.NAME:
        query = query.order("name")  # tie-breaker for equal or missing values
    if limit_by is not None:
        query = query.limit(limit_by)

    try:
        response = query.execute()
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
