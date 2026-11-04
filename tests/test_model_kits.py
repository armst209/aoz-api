"""Response shape, filter mapping and input normalization for /api/v1/model_kits."""

import pytest

from tests.sample_data import KIT_ID, MW_ID, model_kit_row

URL = "/api/v1/model_kits"


def rpc_params(fake_db) -> dict:
    [call] = fake_db.calls("rpc", "search_model_kits")
    return call.params


def test_list_reassembles_nested_model_kit(client, fake_db):
    fake_db.tables["model_kits"] = [model_kit_row()]

    [kit] = client.get(f"{URL}/").json()

    assert kit["id"] == KIT_ID
    assert kit["kitType"] == "Full Kit"
    assert kit["releaseDate"] == "2004-01"
    assert kit["distribution"] == "General Retail"
    # Flat price columns are folded into one object.
    assert kit["price"] == {"amount": 2200, "currency": "JPY", "taxIncluded": False}
    for flat in ("priceAmount", "priceCurrency", "priceTaxIncluded"):
        assert flat not in kit
    assert kit["units"] == [
        {"name": "Hazel Custom", "form": None, "mobileWeaponId": MW_ID, "supportWeaponId": None},
        {"name": "Hazel Custom", "form": "Booster", "mobileWeaponId": None,
         "supportWeaponId": None},
    ]
    assert kit["reissues"] == [{"date": "2010-03", "note": "Recolor"},
                               {"date": "2015-06", "note": None}]


def test_list_kit_without_price_returns_null_price(client, fake_db):
    fake_db.tables["model_kits"] = [model_kit_row(
        price_amount=None, price_currency=None, price_tax_included=None)]

    [kit] = client.get(f"{URL}/").json()

    assert kit["price"] is None


def test_list_handles_missing_child_rows(client, fake_db):
    fake_db.tables["model_kits"] = [model_kit_row(model_kit_units=None, model_kit_reissues=None)]

    [kit] = client.get(f"{URL}/").json()

    assert kit["units"] == []
    assert kit["reissues"] == []


def test_search_returns_reassembled_kits(client, fake_db):
    fake_db.tables["model_kits"] = [model_kit_row()]
    fake_db.rpcs["search_model_kits"] = [{"id": KIT_ID}]

    [kit] = client.get(f"{URL}/search", params={"name": "hazel"}).json()

    assert kit["price"]["amount"] == 2200


@pytest.mark.parametrize("query_param, value, rpc_param", [
    ("name", "hazel", "p_name"),
    ("series", "Advance of Zeta", "p_series"),
    ("line", "HGUC", "p_line"),
    ("grade", "HG", "p_grade"),
    ("manufacturer", "Bandai", "p_manufacturer"),
])
def test_search_maps_text_filters_to_rpc_param(client, fake_db, query_param, value, rpc_param):
    response = client.get(f"{URL}/search", params={query_param: value})

    assert response.status_code == 200
    assert rpc_params(fake_db)[rpc_param] == value


# --- scale --------------------------------------------------------------------

@pytest.mark.parametrize("value, expected", [
    ("1/144", "1/144"),
    ("144", "1/144"),
    ("1:144", "1/144"),
    ("1 / 100", "1/100"),
    ("Mixed", "Mixed"),
])
def test_search_normalizes_scale(client, fake_db, value, expected):
    response = client.get(f"{URL}/search", params={"scale": value})

    assert response.status_code == 200
    assert rpc_params(fake_db)["p_scale"] == expected


# --- releaseDate --------------------------------------------------------------

@pytest.mark.parametrize("value, expected", [
    ("2004", "2004"),
    ("2004-01", "2004-01"),
    ("2004/1", "2004-01"),
    ("2004.01", "2004-01"),
    ("2004-01-15", "2004-01"),
    ("01/2004", "2004-01"),
    ("1-2004", "2004-01"),
    ("Jan 2004", "2004-01"),
    ("January 2004", "2004-01"),
    ("jan. 2004", "2004-01"),
    ("Dec, 2004", "2004-12"),
    ("2004 Jan", "2004-01"),
    ("  2004-03  ", "2004-03"),
])
def test_search_normalizes_release_date(client, fake_db, value, expected):
    response = client.get(f"{URL}/search", params={"releaseDate": value})

    assert response.status_code == 200
    assert rpc_params(fake_db)["p_release_date"] == expected


@pytest.mark.parametrize("value", ["2004-13", "13/2004", "Foo 2004", "yesterday", "04", "2004-00"])
def test_search_rejects_unrecognized_release_date(client, fake_db, value):
    response = client.get(f"{URL}/search", params={"releaseDate": value})

    assert response.status_code == 422
    assert "Unrecognized releaseDate" in response.json()["detail"]
    assert fake_db.executed == []


# --- price --------------------------------------------------------------------

@pytest.mark.parametrize("value, expected", [
    ("2200", 2200.0),
    ("2,200", 2200.0),
    ("¥2200", 2200.0),
    ("¥2,200", 2200.0),
    ("2200 JPY", 2200.0),
    ("1999.5", 1999.5),
])
def test_search_parses_price(client, fake_db, value, expected):
    response = client.get(f"{URL}/search", params={"price": value})

    assert response.status_code == 200
    assert rpc_params(fake_db)["p_price"] == expected


@pytest.mark.parametrize("value", ["free", "0", "¥0"])
def test_search_rejects_unrecognized_price(client, fake_db, value):
    response = client.get(f"{URL}/search", params={"price": value})

    assert response.status_code == 422
    assert "Unrecognized price" in response.json()["detail"]
    assert fake_db.executed == []


def test_search_combines_normalized_filters(client, fake_db):
    client.get(f"{URL}/search", params={"scale": "144", "releaseDate": "2004", "limit": 10})

    assert rpc_params(fake_db) == {
        "p_id": None, "p_name": None, "p_series": None, "p_line": None, "p_grade": None,
        "p_scale": "1/144", "p_manufacturer": None, "p_release_date": "2004", "p_price": None,
        "p_threshold": 0.3, "p_limit": 10,
    }


@pytest.mark.parametrize("order_by, expected", [
    ("name", [("name", {"nullsfirst": False})]),
    ("scale", [("scale_sort", {"nullsfirst": False}), ("name", {})]),
    ("grade", [("grade_sort", {"nullsfirst": False}), ("name", {})]),
])
def test_list_orders_by_sortable_column(client, fake_db, order_by, expected):
    client.get(f"{URL}/", params={"order_by": order_by})

    [query] = fake_db.calls("table", "model_kits")
    assert query.orders == expected
    assert query.limit_to is None


def test_list_applies_limit(client, fake_db):
    client.get(f"{URL}/", params={"limit_by": 5})

    [query] = fake_db.calls("table", "model_kits")
    assert query.limit_to == 5


@pytest.mark.parametrize("params", [{"order_by": "price"}, {"limit_by": 0}])
def test_list_rejects_bad_ordering_params(client, params):
    assert client.get(f"{URL}/", params=params).status_code == 422
