from fastapi.testclient import TestClient

import app.main as main_module
from app.main import app


client = TestClient(app)


def test_incremental_learning_retrain_endpoint(monkeypatch):
    monkeypatch.setattr(
        main_module,
        "retrain_incremental_from_feedback",
        lambda min_frequency=2: {
            "lexicon_path": "data/models/incremental_lexicon.json",
            "updated_entries": 3,
            "feedback_records": 10,
        },
    )
    response = client.post("/api/v1/incremental-learning/retrain", json={"min_frequency": 2})
    assert response.status_code == 200
    payload = response.json()
    assert payload["updated_entries"] == 3
    assert payload["status"] == "success"
