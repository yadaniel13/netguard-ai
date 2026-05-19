"""Integration tests for the NetGuard AI REST API."""

import io
import pytest
from fastapi.testclient import TestClient

from app.main import app
from database.database import init_db

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_db():
    init_db()


def test_index_page():
    """Dashboard page should return 200."""
    res = client.get("/")
    assert res.status_code == 200
    assert "NetGuard" in res.text


def test_upload_page():
    """Upload page should render without errors."""
    res = client.get("/upload")
    assert res.status_code == 200


def test_history_page():
    res = client.get("/history")
    assert res.status_code == 200


def test_models_page():
    res = client.get("/models")
    assert res.status_code == 200


def test_statistics_endpoint():
    res = client.get("/api/statistics")
    assert res.status_code == 200
    data = res.json()
    assert "summary" in data


def test_upload_non_csv():
    """Uploading a non-CSV should return 400."""
    res = client.post(
        "/api/upload",
        files={"file": ("test.txt", b"hello", "text/plain")},
    )
    assert res.status_code == 400


def test_upload_valid_csv():
    """Valid CSV should be accepted and return file_id."""
    csv_content = (
        "Flow Duration,Total Fwd Packets,Total Backward Packets,"
        "Flow Bytes/s,Flow Packets/s,Packet Length Mean,Label\n"
        "1000,5,3,5000.0,100.0,200.0,BENIGN\n"
        "500,2,1,200000.0,5000.0,100.0,DoS Hulk\n"
        "200,1,0,1000.0,200.0,60.0,PortScan\n"
    )
    res = client.post(
        "/api/upload",
        files={"file": ("traffic.csv", csv_content.encode(), "text/csv")},
    )
    assert res.status_code == 200
    data = res.json()
    assert "file_id" in data
    assert data["file_id"] > 0


def test_analysis_not_found():
    res = client.get("/api/analysis/999999")
    assert res.status_code == 404


def test_report_not_found():
    res = client.get("/api/report/999999/csv")
    assert res.status_code == 404
