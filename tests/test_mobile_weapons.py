"""Response shape and filter mapping for /api/v1/mobile_weapons."""

import pytest

from tests.sample_data import MW_ID, mobile_weapon_row

URL = "/api/v1/mobile_weapons"


def test_list_reassembles_nested_mobile_weapon(client, fake_db):
    fake_db.tables["mobile_weapons"] = [mobile_weapon_row()]

    [weapon] = client.get(f"{URL}/").json()

    assert weapon["id"] == MW_ID
    assert weapon["modelNumber"] == "RX-121"
    assert weapon["unitType"] == "Mobile Suit"
    assert weapon["imageUrl"] == "https://example.com/hazel.png"
    # Specs: foreign key dropped, mixed number/text values kept.
    assert "mobileWeaponId" not in weapon["specs"]
    assert weapon["specs"]["heightM"] == 18.5
    assert weapon["specs"]["weightT"] == "38.3 (+410 kW)"
    assert weapon["specs"]["armor"] == ["Gundarium Alloy"]
    # Category rows are grouped and sorted by position.
    assert weapon["equipment"] == {"standard": ["Sensor", "Shield"], "optional": ["Booster"]}
    assert weapon["armaments"] == {"fixed": [], "handheld": ["Beam Rifle"],
                                   "optionalFixed": [], "optionalHandheld": ["Long Rifle"]}
    assert weapon["images"] == [{"file": "front.png", "caption": "Front view"},
                                {"file": "back.png", "caption": None}]


def test_list_handles_missing_child_rows(client, fake_db):
    fake_db.tables["mobile_weapons"] = [mobile_weapon_row(
        mobile_weapon_specs=None, mobile_weapon_equipment=None,
        mobile_weapon_armaments=None, mobile_weapon_images=None)]

    response = client.get(f"{URL}/")

    assert response.status_code == 200
    [weapon] = response.json()
    assert weapon["specs"]["armor"] == []
    assert weapon["specs"]["heightM"] is None
    assert weapon["equipment"] == {"standard": [], "optional": []}
    assert weapon["images"] == []


def test_list_selects_every_child_table(client, fake_db):
    client.get(f"{URL}/")

    [query] = fake_db.calls("table", "mobile_weapons")
    for child in ("mobile_weapon_specs", "mobile_weapon_equipment",
                  "mobile_weapon_armaments", "mobile_weapon_images"):
        assert child in query.select_columns


def test_search_returns_reassembled_weapons(client, fake_db):
    fake_db.tables["mobile_weapons"] = [mobile_weapon_row()]
    fake_db.rpcs["search_mobile_weapons"] = [{"id": MW_ID}]

    [weapon] = client.get(f"{URL}/search", params={"name": "hazle"}).json()

    assert weapon["name"] == "Gundam TR-1 [Hazel]"
    assert weapon["equipment"]["standard"] == ["Sensor", "Shield"]


@pytest.mark.parametrize("query_param, value, rpc_param", [
    ("name", "hazel", "p_name"),
    ("modelNumber", "RX-121", "p_model_number"),
    ("codename", "Hazel", "p_codename"),
    ("faction", "Titans", "p_faction"),
    ("era", "UC", "p_era"),
    ("pilots", "Eliot", "p_pilot"),
])
def test_search_maps_each_filter_to_rpc_param(client, fake_db, query_param, value, rpc_param):
    response = client.get(f"{URL}/search", params={query_param: value})

    assert response.status_code == 200
    [call] = fake_db.calls("rpc", "search_mobile_weapons")
    assert call.params[rpc_param] == value


def test_search_combines_filters(client, fake_db):
    client.get(f"{URL}/search", params={"faction": "Titans", "era": "UC", "limit": 5})

    [call] = fake_db.calls("rpc", "search_mobile_weapons")
    assert call.params == {
        "p_id": None, "p_name": None, "p_model_number": None, "p_codename": None,
        "p_faction": "Titans", "p_era": "UC", "p_pilot": None,
        "p_threshold": 0.3, "p_limit": 5,
    }
