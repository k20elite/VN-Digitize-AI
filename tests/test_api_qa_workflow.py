from fastapi.testclient import TestClient

import app.main as main_module
from app.main import app


client = TestClient(app)


def _kie_field(value, confidence=0.9):
    return {"value": value, "confidence": confidence}


def _kie_document():
    return {
        "so_van_ban": _kie_field("12/2026/QD-UBND", 0.93),
        "ngay_ban_hanh": _kie_field("05/04/2026", 0.88),
        "co_quan_ban_hanh": _kie_field("UBND TP HA NOI", 0.52),
        "loai_van_ban": _kie_field("Quyet dinh", 0.94),
        "trich_yeu": _kie_field("Phe duyet du an", 0.76),
        "custom_fields": {},
        "model_used": None,
    }


def test_qa1_review_create_flags_low_confidence(monkeypatch):
    def fake_run_ocr_fulltext(input_paths, lang, psm, oem):
        return {
            "total_pages": 1,
            "pages": [
                {
                    "input_path": input_paths[0],
                    "full_text": "abc",
                    "lines": [
                        {"text": "UBND TP HA NOI", "bbox": [10, 10, 100, 20], "confidence": 91.0}
                    ],
                }
            ],
        }

    def fake_extract_kie_from_pages(ocr_pages, model, ollama_url, use_llm, template):
        return {
            "pages": [{"kie": _kie_document()}],
            "document": _kie_document(),
        }

    monkeypatch.setattr(main_module, "run_ocr_fulltext", fake_run_ocr_fulltext)
    monkeypatch.setattr(main_module, "extract_kie_from_pages", fake_extract_kie_from_pages)

    response = client.post("/api/v1/qa1/review-create", json={"input_paths": ["a.png"]})
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "QA1_IN_PROGRESS"
    low_conf_fields = payload["split_view"]["low_confidence_fields"]
    assert any(item["field_name"] == "co_quan_ban_hanh" and item["highlight_color"] == "red" for item in low_conf_fields)
    assert any(item["field_name"] == "trich_yeu" and item["highlight_color"] == "yellow" for item in low_conf_fields)


def test_qa2_reject_rolls_back_to_qa1(monkeypatch):
    def fake_run_ocr_fulltext(input_paths, lang, psm, oem):
        return {"total_pages": 1, "pages": [{"input_path": input_paths[0], "full_text": "abc", "lines": []}]}

    def fake_extract_kie_from_pages(ocr_pages, model, ollama_url, use_llm, template):
        return {"pages": [{"kie": _kie_document()}], "document": _kie_document()}

    monkeypatch.setattr(main_module, "run_ocr_fulltext", fake_run_ocr_fulltext)
    monkeypatch.setattr(main_module, "extract_kie_from_pages", fake_extract_kie_from_pages)

    create_resp = client.post("/api/v1/qa1/review-create", json={"input_paths": ["a.png"]})
    session_id = create_resp.json()["session_id"]

    reject_resp = client.post(
        "/api/v1/qa2/decision",
        json={
            "session_id": session_id,
            "action": "reject",
            "reason": "Need correction",
            "rollback_stage": "QA1",
        },
    )
    assert reject_resp.status_code == 200
    payload = reject_resp.json()
    assert payload["status"] == "REJECTED"
    assert payload["rollback_stage"] == "QA1"
