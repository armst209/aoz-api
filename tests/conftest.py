"""Shared fixtures: a TestClient wired to an in-memory fake of the Supabase client.

The routes import a module-level ``supabase`` client from ``app.db``. Each test
swaps that client for ``FakeSupabase`` so no test ever touches the network.
"""

import copy
import os
from types import SimpleNamespace

import pytest

# app.db builds a real client at import time, which needs a URL and a key.
# These dummy values are never used to make a request.
os.environ.setdefault("SUPABASE_URL", "https://test-project.supabase.co")
os.environ.setdefault(
    "SUPABASE_KEY", "eyJhbGciOiJIUzI1NiJ9.eyJyb2xlIjoiYW5vbiJ9.test-signature")

from fastapi.testclient import TestClient  # noqa: E402
from postgrest.exceptions import APIError  # noqa: E402

from app.main import app  # noqa: E402
from app.routes import characters, mobile_weapons, model_kits, support_weapons  # noqa: E402

ROUTE_MODULES = (characters, mobile_weapons, model_kits, support_weapons)


class FakeQuery:
    """A chainable stand-in for a PostgREST table query or RPC call."""

    def __init__(self, db: "FakeSupabase", kind: str, name: str, params: dict | None = None):
        self.db = db
        self.kind = kind
        self.name = name
        self.params = params
        self.select_columns: str | None = None
        self.order_by: str | None = None
        self.orders: list[tuple[str, dict]] = []
        self.limit_to: int | None = None
        self.in_filter: tuple[str, list] | None = None

    def select(self, columns: str) -> "FakeQuery":
        self.select_columns = columns
        return self

    def order(self, column: str, **options) -> "FakeQuery":
        if self.order_by is None:
            self.order_by = column
        self.orders.append((column, options))
        return self

    def limit(self, size: int) -> "FakeQuery":
        self.limit_to = size
        return self

    def in_(self, column: str, values: list) -> "FakeQuery":
        self.in_filter = (column, list(values))
        return self

    def execute(self) -> SimpleNamespace:
        self.db.executed.append(self)
        key = (self.kind, self.name)
        if key in self.db.errors:
            raise self.db.errors[key]

        store = self.db.tables if self.kind == "table" else self.db.rpcs
        # Deep copy so the route's in-place pops can't leak between calls.
        rows = copy.deepcopy(store.get(self.name, []))
        if self.in_filter:
            column, values = self.in_filter
            rows = [row for row in rows if row[column] in values]
        return SimpleNamespace(data=rows)


class FakeSupabase:
    """Holds canned table rows and RPC results, and records every executed query."""

    def __init__(self):
        self.tables: dict[str, list[dict]] = {}
        self.rpcs: dict[str, list[dict]] = {}
        self.errors: dict[tuple[str, str], Exception] = {}
        self.executed: list[FakeQuery] = []

    def table(self, name: str) -> FakeQuery:
        return FakeQuery(self, "table", name)

    def rpc(self, name: str, params: dict) -> FakeQuery:
        return FakeQuery(self, "rpc", name, params)

    # Helpers for tests.
    def fail(self, kind: str, name: str, message: str = "upstream exploded") -> None:
        """Make the next execute() of this table/RPC raise a PostgREST APIError."""
        self.errors[(kind, name)] = APIError({"message": message, "code": "XX000"})

    def calls(self, kind: str, name: str | None = None) -> list[FakeQuery]:
        return [q for q in self.executed if q.kind == kind and (name is None or q.name == name)]


@pytest.fixture
def fake_db(monkeypatch) -> FakeSupabase:
    db = FakeSupabase()
    for module in ROUTE_MODULES:
        monkeypatch.setattr(module, "supabase", db)
    return db


@pytest.fixture
def client(fake_db) -> TestClient:
    return TestClient(app)
