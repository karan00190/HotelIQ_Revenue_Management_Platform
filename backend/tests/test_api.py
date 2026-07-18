"""API integration smoke tests using FastAPI's TestClient.

The whole app is wired up and hit over HTTP, but get_db is overridden to yield
the seeded in-memory session so requests read the same hand-countable data as
the service tests. TestClient is used WITHOUT its context-manager form on
purpose, so the app's lifespan (which would run init_db against the real
engine) never fires - the fixture already created the schema.
"""

import pytest
from fastapi.testclient import TestClient

from app.database.connection import get_db
from app.main import app


@pytest.fixture
def client(db):
    app.dependency_overrides[get_db] = lambda: db
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_list_hotels(client):
    resp = client.get("/hotels/")
    assert resp.status_code == 200
    body = resp.json()
    assert len(body) == 2
    assert {h["name"] for h in body} == {"Grand Plaza", "Coastal Inn"}


def test_total_revenue_endpoint(client):
    resp = client.get("/smart-queries/total-revenue", params={"hotel_id": 1})
    assert resp.status_code == 200
    body = resp.json()
    assert body["total_revenue"] == 27000
    assert body["total_bookings"] == 3


def test_assistant_status_shape(client):
    # Doesn't require a real LLM key - just that the status contract holds.
    resp = client.get("/assistant/status")
    assert resp.status_code == 200
    body = resp.json()
    assert set(body) >= {"configured", "model", "knowledge_available", "knowledge_chunks"}
    assert isinstance(body["configured"], bool)
