"""Response shape and filter mapping for /api/v1/support_weapons."""

import pytest

from tests.sample_data import SW_ID, support_weapon_row

URL = "/api/v1/support_weapons"


def test_list_reassembles_nested_support_weapon(client, fake_db):
    fake_db.tables["support_weapons"] = [support_weapon_row()]

    [weapon] = client.get(f"{URL}/").json()

    assert weapon["id"] == SW_ID
    assert weapon["category"] == "Ship"
    assert weapon["classification"] == "Heavy Cruiser"
    assert weapon["captains"] == ["Ourdin Saeki"]
    assert "supportWeaponId" not in weapon["specs"]
    assert weapon["specs"]["lengthM"] == 316
    assert weapon["specs"]["propulsion"] == ["Rocket"]
    assert weapon["mobileSuitOperations"] == {
        "hangars": 2,
        "catapults": 2,
        "capacity": "8-12",
        "complement": [
            {"group": "Escort", "units": ["Hizack", "Marasai"]},
            {"group": "T3", "units": ["Hazel II"]},
        ],
    }
    assert weapon["equipment"] == {"standard": ["Radar"], "optional": []}
    assert weapon["armaments"]["fixed"] == ["Mega Particle Cannon", "Missile Launcher"]
    assert weapon["images"] == [{"file": "alexandria.png", "caption": None}]


def test_list_handles_missing_child_rows(client, fake_db):
    fake_db.tables["support_weapons"] = [support_weapon_row(
        support_weapon_specs=None, support_weapon_ms_operations=None,
        support_weapon_complement=None, support_weapon_equipment=None,
        support_weapon_armaments=None, support_weapon_images=None)]

    response = client.get(f"{URL}/")

    assert response.status_code == 200
    [weapon] = response.json()
    assert weapon["specs"]["propulsion"] == []
    assert weapon["mobileSuitOperations"] == {
        "hangars": None, "catapults": None, "capacity": None, "complement": []}
    assert weapon["armaments"]["fixed"] == []
    assert weapon["images"] == []


def test_list_selects_every_child_table(client, fake_db):
    client.get(f"{URL}/")

    [query] = fake_db.calls("table", "support_weapons")
    for child in ("support_weapon_specs", "support_weapon_ms_operations",
                  "support_weapon_complement", "support_weapon_equipment",
                  "support_weapon_armaments", "support_weapon_images"):
        assert child in query.select_columns


def test_search_returns_reassembled_weapons(client, fake_db):
    fake_db.tables["support_weapons"] = [support_weapon_row()]
    fake_db.rpcs["search_support_weapons"] = [{"id": SW_ID}]

    [weapon] = client.get(f"{URL}/search", params={"name": "alexandra"}).json()

    assert weapon["name"] == "Alexandria"
    assert weapon["mobileSuitOperations"]["hangars"] == 2


@pytest.mark.parametrize("query_param, value, rpc_param", [
    ("name", "alexandria", "p_name"),
    ("modelNumber", "AL-01", "p_model_number"),
    ("codename", "Alex", "p_codename"),
    ("faction", "Titans", "p_faction"),
    ("era", "UC", "p_era"),
    ("pilots", "Ourdin", "p_pilot"),
])
def test_search_maps_each_filter_to_rpc_param(client, fake_db, query_param, value, rpc_param):
    response = client.get(f"{URL}/search", params={query_param: value})

    assert response.status_code == 200
    [call] = fake_db.calls("rpc", "search_support_weapons")
    assert call.params[rpc_param] == value


@pytest.mark.parametrize("order_by, expected", [
    ("name", [("name", {"nullsfirst": False})]),
    ("model_number", [("model_number", {"nullsfirst": False}), ("name", {})]),
    ("modelNumber", [("model_number", {"nullsfirst": False}), ("name", {})]),
])
def test_list_orders_by_sortable_column(client, fake_db, order_by, expected):
    client.get(f"{URL}/", params={"order_by": order_by})

    [query] = fake_db.calls("table", "support_weapons")
    assert query.orders == expected
    assert query.limit_to is None


def test_list_applies_limit(client, fake_db):
    client.get(f"{URL}/", params={"limit_by": 5})

    [query] = fake_db.calls("table", "support_weapons")
    assert query.limit_to == 5


@pytest.mark.parametrize("params", [{"order_by": "era"}, {"limit_by": 0}])
def test_list_rejects_bad_ordering_params(client, params):
    assert client.get(f"{URL}/", params=params).status_code == 422
