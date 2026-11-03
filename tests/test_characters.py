"""Response shape and filter mapping for /api/v1/characters."""

import pytest

from tests.sample_data import CHAR_ID, MW_ID, SW_ID, character_row

URL = "/api/v1/characters"


def test_list_reassembles_nested_character(client, fake_db):
    fake_db.tables["characters"] = [character_row()]

    [character] = client.get(f"{URL}/").json()

    assert character["id"] == CHAR_ID
    assert character["slug"] == "eliot-lemon"
    assert character["japaneseName"] == "エリアルド・ハンター"
    assert character["group"] == "Titans Test Team (T3)"
    assert character["age"] == 23
    assert character["hasWikiPage"] is True
    # Child rows are sorted by position and lose the position column.
    assert character["associatedUnits"] == [
        {"name": "Gundam TR-1 [Hazel]", "role": "pilot", "note": "Test pilot",
         "mobileWeaponId": MW_ID, "supportWeaponId": None},
        {"name": "Alexandria", "role": "crew", "note": None,
         "mobileWeaponId": None, "supportWeaponId": SW_ID},
    ]
    assert character["images"] == [{"file": "eliot.png", "caption": "Portrait"}]


def test_list_handles_missing_child_rows(client, fake_db):
    fake_db.tables["characters"] = [character_row(
        character_associated_units=None, character_images=None)]

    [character] = client.get(f"{URL}/").json()

    assert character["associatedUnits"] == []
    assert character["images"] == []


def test_list_accepts_text_age(client, fake_db):
    fake_db.tables["characters"] = [character_row(age="23 (U.C. 0084)")]

    [character] = client.get(f"{URL}/").json()

    assert character["age"] == "23 (U.C. 0084)"


def test_search_returns_reassembled_characters(client, fake_db):
    fake_db.tables["characters"] = [character_row()]
    fake_db.rpcs["search_characters"] = [{"id": CHAR_ID}]

    [character] = client.get(f"{URL}/search", params={"name": "eliott"}).json()

    assert character["name"] == "Eliot Lemon"
    assert character["associatedUnits"][0]["role"] == "pilot"


@pytest.mark.parametrize("query_param, value, rpc_param", [
    ("name", "eliot", "p_name"),
    ("japaneseName", "エリアルド", "p_japanese_name"),
    ("gender", "Male", "p_gender"),
    ("birthdate", "U.C. 0064", "p_birthdate"),
    ("deathdate", "U.C. 0088", "p_deathdate"),
    ("status", "Alive", "p_status"),
    ("affiliations", "Titans", "p_affiliation"),
    ("rank", "Ensign", "p_rank"),
    ("age", "23", "p_age"),
])
def test_search_maps_each_filter_to_rpc_param(client, fake_db, query_param, value, rpc_param):
    response = client.get(f"{URL}/search", params={query_param: value})

    assert response.status_code == 200
    [call] = fake_db.calls("rpc", "search_characters")
    assert call.params[rpc_param] == value
