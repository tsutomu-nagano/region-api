import os
import sys
import tempfile
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

TEST_DB = Path(tempfile.gettempdir()) / "region-api-test.db"
if TEST_DB.exists():
    TEST_DB.unlink()
os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB}"

from fastapi.testclient import TestClient  # noqa: E402

from database import SessionLocal  # noqa: E402
from importer import refresh_from_csv  # noqa: E402
from main import app  # noqa: E402
import models  # noqa: E402


def seed_test_database():
    db = SessionLocal()
    try:
        refreshed, states = refresh_from_csv(db, force=True)
        assert refreshed is True
        assert {state.source_name: state.row_count for state in states} == {
            "municipality": 1919,
            "merger": 3507,
        }
    finally:
        db.close()


def test_refresh_from_csv_imports_expected_rows_and_skips_when_unchanged():
    seed_test_database()

    db = SessionLocal()
    try:
        municipality_count = db.query(models.Municipality).count()
        merger_count = db.query(models.Merger).count()
        refreshed, states = refresh_from_csv(db)

        assert municipality_count == 1919
        assert merger_count == 3507
        assert refreshed is False
        assert {state.source_name: state.row_count for state in states} == {
            "municipality": 1919,
            "merger": 3507,
        }
    finally:
        db.close()


def test_municipality_parent_relationship_is_available_from_api():
    seed_test_database()

    with TestClient(app) as client:
        sapporo = client.get("/api/v1/municipalities/01100")
        chuo = client.get("/api/v1/municipalities/01101")
        children = client.get("/api/v1/municipalities/01100/children")
        filtered_children = client.get("/api/v1/municipalities", params={"parent_code": "01100", "limit": 20})

    assert sapporo.status_code == 200
    assert chuo.status_code == 200
    assert children.status_code == 200
    assert filtered_children.status_code == 200

    assert sapporo.json()["parent_code"] is None
    assert chuo.json()["parent_code"] == "01100"

    child_codes = [item["code"] for item in children.json()]
    filtered_child_codes = [item["code"] for item in filtered_children.json()]

    assert "01101" in child_codes
    assert len(child_codes) == 10
    assert filtered_child_codes == child_codes


def test_mergers_api_returns_csv_backed_rows():
    seed_test_database()

    with TestClient(app) as client:
        response = client.get("/api/v1/mergers", params={"limit": 1})

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["code"]
    assert response.json()[0]["reason"]


def test_refresh_endpoint_is_not_exposed():
    with TestClient(app) as client:
        openapi = client.get("/openapi.json")
        response = client.post("/api/v1/sources/refresh")

    assert openapi.status_code == 200
    assert "/api/v1/sources/refresh" not in openapi.json()["paths"]
    assert response.status_code == 404
