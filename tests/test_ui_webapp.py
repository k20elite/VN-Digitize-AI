from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_ui_page_is_served():
    response = client.get("/ui")
    assert response.status_code == 200
    assert "SỐ HÓA OCR (7 BƯỚC)" in response.text


def test_debug_file_endpoint_serves_existing_file(tmp_path: Path):
    file_path = tmp_path / "debug.txt"
    file_path.write_text("debug-content", encoding="utf-8")

    response = client.get("/api/v1/debug/file", params={"path": str(file_path)})
    assert response.status_code == 200
    assert response.text == "debug-content"
