"""Behavior shared by every resource's list and search endpoints."""

import pytest

from tests import sample_data as sample

ID_A = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
ID_B = "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb"
ID_C = "cccccccc-cccc-4ccc-8ccc-cccccccccccc"

# (url prefix, table name, search RPC name, row builder, a valid search filter)
RESOURCES = {
    "mobile_weapons": ("/api/v1/mobile_weapons", "mobile_weapons", "search_mobile_weapons",
                       sample.mobile_weapon_row, {"name": "hazel"}),
    "support_weapons": ("/api/v1/support_weapons", "support_weapons", "search_support_weapons",
                        sample.support_weapon_row, {"name": "alexandria"}),
    "characters": ("/api/v1/characters", "characters", "search_characters",
                   sample.character_row, {"name": "eliot"}),
    "model_kits": ("/api/v1/model_kits", "model_kits", "search_model_kits",
                   sample.model_kit_row, {"name": "hazel"}),
}


@pytest.fixture(params=RESOURCES.values(), ids=RESOURCES.keys())
def resource(request):
    prefix, table, rpc, make_row, search_filter = request.param
    return {"prefix": prefix, "table": table, "rpc": rpc, "make_row": make_row,
            "filter": search_filter}


# --- GET /<resource>/ ---------------------------------------------------------

def test_list_returns_all_rows_ordered_by_name(client, fake_db, resource):
    make_row = resource["make_row"]
    fake_db.tables[resource["table"]] = [make_row(id=ID_A, name="Alpha"),
                                         make_row(id=ID_B, name="Beta")]

    response = client.get(f"{resource['prefix']}/")

    assert response.status_code == 200
    assert [item["id"] for item in response.json()] == [ID_A, ID_B]
    [query] = fake_db.calls("table", resource["table"])
    assert query.order_by == "name"
    assert query.select_columns.startswith("*,")


def test_list_empty_table_returns_empty_list(client, resource):
    response = client.get(f"{resource['prefix']}/")

    assert response.status_code == 200
    assert response.json() == []


def test_list_upstream_error_returns_502(client, fake_db, resource):
    fake_db.fail("table", resource["table"], "connection refused")

    response = client.get(f"{resource['prefix']}/")

    assert response.status_code == 502
    assert response.json() == {"detail": "connection refused"}


# --- GET /<resource>/search ---------------------------------------------------

def test_search_requires_at_least_one_filter(client, fake_db, resource):
    response = client.get(f"{resource['prefix']}/search")

    assert response.status_code == 400
    assert response.json() == {"detail": "Provide at least one search filter"}
    assert fake_db.executed == []


def test_search_threshold_and_limit_alone_are_not_filters(client, resource):
    response = client.get(f"{resource['prefix']}/search", params={"threshold": 0.5, "limit": 5})

    assert response.status_code == 400


def test_search_results_keep_the_search_ranking(client, fake_db, resource):
    make_row = resource["make_row"]
    # The table returns rows in a different order from the RPC's ranking.
    fake_db.tables[resource["table"]] = [make_row(id=ID_A, name="A"), make_row(id=ID_B, name="B"),
                                         make_row(id=ID_C, name="C")]
    fake_db.rpcs[resource["rpc"]] = [{"id": ID_C}, {"id": ID_A}]

    response = client.get(f"{resource['prefix']}/search", params=resource["filter"])

    assert response.status_code == 200
    assert [item["id"] for item in response.json()] == [ID_C, ID_A]
    [query] = fake_db.calls("table", resource["table"])
    assert query.in_filter == ("id", [ID_C, ID_A])


def test_search_uses_default_threshold_and_limit(client, fake_db, resource):
    client.get(f"{resource['prefix']}/search", params=resource["filter"])

    [call] = fake_db.calls("rpc", resource["rpc"])
    assert call.params["p_threshold"] == 0.3
    assert call.params["p_limit"] == 20


def test_search_passes_custom_threshold_and_limit(client, fake_db, resource):
    client.get(f"{resource['prefix']}/search",
               params={**resource["filter"], "threshold": 0.7, "limit": 5})

    [call] = fake_db.calls("rpc", resource["rpc"])
    assert call.params["p_threshold"] == 0.7
    assert call.params["p_limit"] == 5


def test_search_unset_filters_are_sent_as_none(client, fake_db, resource):
    client.get(f"{resource['prefix']}/search", params=resource["filter"])

    [call] = fake_db.calls("rpc", resource["rpc"])
    filters = {k: v for k, v in call.params.items() if k not in ("p_threshold", "p_limit")}
    assert [k for k, v in filters.items() if v is not None] == ["p_name"]


def test_search_id_filter_is_sent_as_string(client, fake_db, resource):
    client.get(f"{resource['prefix']}/search", params={"id": ID_A})

    [call] = fake_db.calls("rpc", resource["rpc"])
    assert call.params["p_id"] == ID_A


def test_search_no_matches_skips_table_query(client, fake_db, resource):
    fake_db.rpcs[resource["rpc"]] = []

    response = client.get(f"{resource['prefix']}/search", params=resource["filter"])

    assert response.status_code == 200
    assert response.json() == []
    assert fake_db.calls("table") == []


@pytest.mark.parametrize("bad_params", [
    {"id": "not-a-uuid"},
    {"name": "x", "limit": 0},
    {"name": "x", "limit": 101},
    {"name": "x", "limit": "ten"},
    {"name": "x", "threshold": -0.1},
    {"name": "x", "threshold": 1.1},
])
def test_search_invalid_query_params_return_422(client, fake_db, resource, bad_params):
    response = client.get(f"{resource['prefix']}/search", params=bad_params)

    assert response.status_code == 422
    assert fake_db.executed == []


@pytest.mark.parametrize("params", [{"limit": 1}, {"limit": 100}, {"threshold": 0},
                                    {"threshold": 1}])
def test_search_boundary_values_are_accepted(client, resource, params):
    response = client.get(f"{resource['prefix']}/search", params={**resource["filter"], **params})

    assert response.status_code == 200


def test_search_rpc_error_returns_502(client, fake_db, resource):
    fake_db.fail("rpc", resource["rpc"], "function does not exist")

    response = client.get(f"{resource['prefix']}/search", params=resource["filter"])

    assert response.status_code == 502
    assert response.json() == {"detail": "function does not exist"}


def test_search_table_error_after_rpc_returns_502(client, fake_db, resource):
    fake_db.rpcs[resource["rpc"]] = [{"id": ID_A}]
    fake_db.fail("table", resource["table"], "timeout")

    response = client.get(f"{resource['prefix']}/search", params=resource["filter"])

    assert response.status_code == 502
    assert response.json() == {"detail": "timeout"}
