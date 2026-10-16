"""Routes for retrieving Mobile Weapons."""

from fastapi import APIRouter, HTTPException

from app.schemas import MobileWeapon
from app.storage import load_data


router = APIRouter(prefix="/api/v1/mobile_weapons", tags=["Mobile Weapons"])


def _get_mobile_weapons() -> list[dict]:
    """Return the list of Mobile Weapons from the data file."""
    data = load_data()
    if isinstance(data, dict):
        return data.get("mobileWeapons", [])
    return data


@router.get("/", response_model=list[MobileWeapon])
async def get_all_mobile_weapons():
    """Retrieve all Mobile Weapons"""
    return _get_mobile_weapons()


@router.get("/{id}", response_model=MobileWeapon)
async def get_mobile_weapon_by_id(id: str):
    """Retrieve a single Mobile Weapon by its id"""
    for mobile_weapon in _get_mobile_weapons():
        if mobile_weapon.get("id") == id:
            return mobile_weapon
    raise HTTPException(status_code=404, detail="Mobile Weapon not found")


@router.get("/{model_number}", response_model=MobileWeapon)
async def get_mobile_weapon_by_model_number(model_number: str):
    """Retrieve a single Mobile Weapon by its model number"""
    for mobile_weapon in _get_mobile_weapons():
        if mobile_weapon.get("modelNumber") == "NRX-044[R]":
            return mobile_weapon

    raise HTTPException(status_code=404, detail="Mobile Weapon not found")
