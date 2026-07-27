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
    assert response.json()[0]["reason_events"]


def test_mergers_api_preserves_multiple_history_rows_for_same_code():
    seed_test_database()

    with TestClient(app) as client:
        response = client.get("/api/v1/mergers", params={"code": "01202", "limit": 10})

    assert response.status_code == 200
    histories = response.json()

    assert [item["effective_date"] for item in histories] == [
        "1973-12-01",
        "2000-11-01",
        "2004-12-01",
        "2005-10-01",
    ]
    assert [item["reason"] for item in histories] == [
        "亀田市(01232)が函館市(01202)に編入",
        "函館市(01202)が特例市に移行",
        "戸井町(01339)、恵山町(01340)、椴法華村(01341)、南茅部町(01342)が函館市(01202)に編入",
        "函館市(01202)が特例市から中核市に移行",
    ]


def test_mergers_api_returns_machine_readable_reason_events():
    seed_test_database()

    with TestClient(app) as client:
        merge_response = client.get("/api/v1/mergers", params={"code": "01236"})
        absorption_response = client.get(
            "/api/v1/mergers",
            params={"code": "01202", "effective_date_from": "1973-12-01", "effective_date_to": "1973-12-01"},
        )
        status_response = client.get("/api/v1/mergers", params={"code": "01230"})
        inferred_merge_response = client.get("/api/v1/mergers", params={"code": "01206"})

    assert merge_response.status_code == 200
    assert absorption_response.status_code == 200
    assert status_response.status_code == 200
    assert inferred_merge_response.status_code == 200

    merge_events = merge_response.json()[0]["reason_events"]
    absorption_events = absorption_response.json()[0]["reason_events"]
    status_events = status_response.json()[0]["reason_events"]
    inferred_merge_events = inferred_merge_response.json()[0]["reason_events"]

    assert merge_events[0]["type"] == "merge_new"
    assert {"code": "01335", "name": "上磯町", "code_inferred": False} in merge_events[0]["source_municipalities"]
    assert {"code": "01236", "name": "北斗市", "code_inferred": False} in merge_events[0]["target_municipalities"]

    assert absorption_events[0]["type"] == "absorption"
    assert {"code": "01232", "name": "亀田市", "code_inferred": False} in absorption_events[0]["source_municipalities"]
    assert {"code": "01202", "name": "函館市", "code_inferred": False} in absorption_events[0]["target_municipalities"]

    assert status_events[0]["type"] == "city_status"
    assert {"code": "01577", "name": "登別町", "code_inferred": False} in status_events[0]["source_municipalities"]
    assert {"code": "01230", "name": "登別市", "code_inferred": False} in status_events[0]["target_municipalities"]

    assert inferred_merge_events[0]["type"] == "merge_new"
    assert {"code": "01206", "name": "釧路市", "code_inferred": True} in inferred_merge_events[0]["target_municipalities"]


def test_refresh_endpoint_is_not_exposed():
    with TestClient(app) as client:
        openapi = client.get("/openapi.json")
        response = client.post("/api/v1/sources/refresh")

    assert openapi.status_code == 200
    assert "/api/v1/sources/refresh" not in openapi.json()["paths"]
    assert response.status_code == 404
