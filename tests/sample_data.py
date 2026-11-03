"""Builders for raw Supabase rows, shaped the way PostgREST returns them with embeds.

Child rows are deliberately listed out of ``position`` order so tests can check
that the routes sort them.
"""

MW_ID = "11111111-1111-4111-8111-111111111111"
SW_ID = "22222222-2222-4222-8222-222222222222"
CHAR_ID = "33333333-3333-4333-8333-333333333333"
KIT_ID = "44444444-4444-4444-8444-444444444444"


def mobile_weapon_row(id: str = MW_ID, name: str = "Gundam TR-1 [Hazel]", **overrides) -> dict:
    row = {
        "id": id,
        "name": name,
        "model_number": "RX-121",
        "codename": "Hazel",
        "faction": "Titans",
        "other_names": ["Hazel"],
        "unit_type": "Mobile Suit",
        "production": "Prototype",
        "era": "Universal Century",
        "pilots": ["Eliot Lemon"],
        "image_url": "https://example.com/hazel.png",
        "extra": {},
        "mobile_weapon_specs": {
            "mobile_weapon_id": id,
            "height_m": 18.5,
            "weight_t": "38.3 (+410 kW)",
            "armor": ["Gundarium Alloy"],
            "rocket_thrusters_kg": [],
            "thruster_layout": [],
        },
        "mobile_weapon_equipment": [
            {"category": "standard", "position": 1, "item": "Shield"},
            {"category": "standard", "position": 0, "item": "Sensor"},
            {"category": "optional", "position": 2, "item": "Booster"},
        ],
        "mobile_weapon_armaments": [
            {"category": "optional_handheld", "position": 1, "item": "Long Rifle"},
            {"category": "handheld", "position": 0, "item": "Beam Rifle"},
        ],
        "mobile_weapon_images": [
            {"position": 1, "file": "back.png", "caption": None},
            {"position": 0, "file": "front.png", "caption": "Front view"},
        ],
    }
    row.update(overrides)
    return row


def support_weapon_row(id: str = SW_ID, name: str = "Alexandria", **overrides) -> dict:
    row = {
        "id": id,
        "name": name,
        "model_number": None,
        "codename": None,
        "faction": "Titans",
        "category": "Ship",
        "classification": "Heavy Cruiser",
        "production": "Mass Production",
        "era": "Universal Century",
        "pilots": [],
        "captains": ["Ourdin Saeki"],
        "extra": {},
        "support_weapon_specs": {
            "support_weapon_id": id,
            "length_m": 316,
            "propulsion": ["Rocket"],
            "armor": [],
        },
        "support_weapon_ms_operations": {
            "support_weapon_id": id,
            "hangars": 2,
            "catapults": 2,
            "capacity": "8-12",
        },
        "support_weapon_complement": [
            {"position": 1, "group": "T3", "units": ["Hazel II"]},
            {"position": 0, "group": "Escort", "units": ["Hizack", "Marasai"]},
        ],
        "support_weapon_equipment": [
            {"category": "standard", "position": 0, "item": "Radar"},
        ],
        "support_weapon_armaments": [
            {"category": "fixed", "position": 1, "item": "Missile Launcher"},
            {"category": "fixed", "position": 0, "item": "Mega Particle Cannon"},
        ],
        "support_weapon_images": [
            {"position": 0, "file": "alexandria.png", "caption": None},
        ],
    }
    row.update(overrides)
    return row


def character_row(id: str = CHAR_ID, name: str = "Eliot Lemon", **overrides) -> dict:
    row = {
        "id": id,
        "slug": "eliot-lemon",
        "name": name,
        "japanese_name": "エリアルド・ハンター",
        "group": "Titans Test Team (T3)",
        "gender": "Male",
        "age": 23,
        "status": "Alive",
        "affiliations": ["Titans", "T3"],
        "rank": "Ensign",
        "has_wiki_page": True,
        "character_associated_units": [
            {"position": 1, "name": "Alexandria", "role": "crew", "note": None,
             "mobile_weapon_id": None, "support_weapon_id": SW_ID},
            {"position": 0, "name": "Gundam TR-1 [Hazel]", "role": "pilot", "note": "Test pilot",
             "mobile_weapon_id": MW_ID, "support_weapon_id": None},
        ],
        "character_images": [
            {"position": 0, "file": "eliot.png", "caption": "Portrait"},
        ],
    }
    row.update(overrides)
    return row


def model_kit_row(id: str = KIT_ID, name: str = "HGUC Gundam TR-1 [Hazel Custom]", **overrides) -> dict:
    row = {
        "id": id,
        "name": name,
        "series": "Advance of Zeta",
        "other_series": [],
        "line": "HGUC",
        "grade": "HG",
        "scale": "1/144",
        "kit_type": "Full Kit",
        "material": "Plastic",
        "manufacturer": "Bandai",
        "distribution": "General Retail",
        "exclusive": False,
        "release_date": "2004-01",
        "price_amount": 2200,
        "price_currency": "JPY",
        "price_tax_included": False,
        "transformable": False,
        "based_on": [],
        "requires": [],
        "notes": [],
        "extra": {},
        "model_kit_units": [
            {"position": 1, "name": "Hazel Custom", "form": "Booster", "mobile_weapon_id": None,
             "support_weapon_id": None},
            {"position": 0, "name": "Hazel Custom", "form": None, "mobile_weapon_id": MW_ID,
             "support_weapon_id": None},
        ],
        "model_kit_reissues": [
            {"position": 1, "date": "2015-06", "note": None},
            {"position": 0, "date": "2010-03", "note": "Recolor"},
        ],
    }
    row.update(overrides)
    return row
