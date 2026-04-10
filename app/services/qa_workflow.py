from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4


QA_DIR = Path("data") / "qa_sessions"
QA_DIR.mkdir(parents=True, exist_ok=True)


def _session_path(session_id: str) -> Path:
    return QA_DIR / f"{session_id}.json"


def create_qa_session(payload: dict) -> dict:
    session_id = uuid4().hex
    record = {
        "session_id": session_id,
        "status": "QA1_IN_PROGRESS",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
        **payload,
    }
    _session_path(session_id).write_text(
        json.dumps(record, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return record


def get_qa_session(session_id: str) -> dict | None:
    path = _session_path(session_id)
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def update_qa_session(session_id: str, update: dict) -> dict | None:
    existing = get_qa_session(session_id)
    if existing is None:
        return None
    existing.update(update)
    existing["updated_at"] = datetime.now(timezone.utc).isoformat()
    _session_path(session_id).write_text(
        json.dumps(existing, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return existing
