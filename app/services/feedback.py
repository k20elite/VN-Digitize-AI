import datetime
import json
from pathlib import Path

try:
    from tinydb import TinyDB
except Exception:  # pragma: no cover - optional dependency fallback
    TinyDB = None

DATA_DIR = Path("data")
DATA_DIR.mkdir(parents=True, exist_ok=True)
FEEDBACK_DB_PATH = DATA_DIR / "feedback.json"

def _append_feedback_json(record: dict) -> int:
    if FEEDBACK_DB_PATH.exists():
        try:
            existing = json.loads(FEEDBACK_DB_PATH.read_text(encoding="utf-8"))
        except Exception:
            existing = []
    else:
        existing = []
    if not isinstance(existing, list):
        existing = []
    existing.append(record)
    FEEDBACK_DB_PATH.write_text(
        json.dumps(existing, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return len(existing)

def save_feedback(original_text: str, corrected_text: str, field_name: str, document_id: str = "unknown") -> int:
    """
    Saves a record of AI extraction mistake corrected by QA personnel.
    """
    record = {
        "document_id": document_id,
        "field_name": field_name,
        "original_text": original_text,
        "corrected_text": corrected_text,
        "created_at": datetime.datetime.now().isoformat()
    }
    if TinyDB is not None:
        with TinyDB(FEEDBACK_DB_PATH) as db:
            return db.insert(record)
    return _append_feedback_json(record)

def get_all_feedback() -> list[dict]:
    if TinyDB is not None:
        with TinyDB(FEEDBACK_DB_PATH) as db:
            return db.all()
    if not FEEDBACK_DB_PATH.exists():
        return []
    try:
        data = json.loads(FEEDBACK_DB_PATH.read_text(encoding="utf-8"))
    except Exception:
        return []
    return data if isinstance(data, list) else []
