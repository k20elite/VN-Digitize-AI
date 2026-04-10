from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from pathlib import Path

from app.services.feedback import get_all_feedback


MODEL_DIR = Path("data") / "models"
MODEL_DIR.mkdir(parents=True, exist_ok=True)
DEFAULT_LEXICON_PATH = MODEL_DIR / "incremental_lexicon.json"


def _normalize_phrase(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").strip().lower())


def retrain_incremental_from_feedback(
    *,
    output_dir: Path | None = None,
    min_frequency: int = 2,
) -> dict:
    feedback_rows = get_all_feedback()
    grouped: dict[str, Counter[str]] = defaultdict(Counter)
    for row in feedback_rows:
        src = _normalize_phrase(str(row.get("original_text", "")))
        dst = _normalize_phrase(str(row.get("corrected_text", "")))
        if not src or not dst:
            continue
        grouped[src][dst] += 1

    lexicon: dict[str, str] = {}
    for src, counter in grouped.items():
        best_dst, freq = counter.most_common(1)[0]
        if freq >= max(1, min_frequency):
            lexicon[src] = best_dst

    target_dir = output_dir or MODEL_DIR
    target_dir.mkdir(parents=True, exist_ok=True)
    lexicon_path = target_dir / "incremental_lexicon.json"
    lexicon_path.write_text(
        json.dumps(lexicon, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return {
        "lexicon_path": str(lexicon_path),
        "updated_entries": len(lexicon),
        "feedback_records": len(feedback_rows),
    }


def _load_lexicon(lexicon_path: Path | None = None) -> dict[str, str]:
    path = lexicon_path or DEFAULT_LEXICON_PATH
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return data if isinstance(data, dict) else {}


def apply_incremental_lexicon(text: str, *, lexicon_path: Path | None = None) -> str:
    if not text:
        return text
    lexicon = _load_lexicon(lexicon_path)
    if not lexicon:
        return text

    updated = text
    lowered = text.lower()
    for src, dst in sorted(lexicon.items(), key=lambda item: len(item[0]), reverse=True):
        if src and src in lowered:
            updated = re.sub(re.escape(src), dst, updated, flags=re.IGNORECASE)
            lowered = updated.lower()
    return updated


def get_incremental_status(*, lexicon_path: Path | None = None) -> dict:
    path = lexicon_path or DEFAULT_LEXICON_PATH
    lexicon = _load_lexicon(path)
    return {
        "lexicon_path": str(path),
        "updated_entries": len(lexicon),
        "feedback_records": len(get_all_feedback()),
    }
