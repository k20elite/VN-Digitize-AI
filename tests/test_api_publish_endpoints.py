from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_download_exported_pdf_returns_file(tmp_path: Path):
    exported_dir = Path("data") / "exported"
    exported_dir.mkdir(parents=True, exist_ok=True)
    filename = "unit_test_download.pdf"
    file_path = exported_dir / filename
    file_path.write_bytes(b"PDF")

    response = client.get(f"/api/v1/downloads/{filename}")
    assert response.status_code == 200
    assert response.content == b"PDF"


def test_archive_store_copies_file(tmp_path: Path):
    source = tmp_path / "source.pdf"
    source.write_bytes(b"PDF-A")

    response = client.post(
        "/api/v1/archive/store",
        json={"input_path": str(source), "document_id": "doc-001"},
    )
    assert response.status_code == 200
    payload = response.json()
    archived_path = Path(payload["archived_path"])
    assert archived_path.exists()
    assert archived_path.read_bytes() == b"PDF-A"
