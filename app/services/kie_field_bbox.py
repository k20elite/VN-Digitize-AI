from __future__ import annotations

import re
import unicodedata
from difflib import SequenceMatcher
from typing import Any


def _normalize_text(text: str) -> str:
    lowered = (text or "").strip().lower()
    if not lowered:
        return ""
    normalized = unicodedata.normalize("NFD", lowered)
    normalized = "".join(ch for ch in normalized if unicodedata.category(ch) != "Mn")
    normalized = re.sub(r"\s+", " ", normalized)
    return normalized


def _line_match_score(field_text: str, line_text: str) -> float:
    if not field_text or not line_text:
        return 0.0
    if field_text in line_text:
        return 1.0
    if line_text in field_text and len(line_text) >= 8:
        return 0.85
    return SequenceMatcher(a=field_text, b=line_text).ratio()


def _extract_field_values(kie_result: dict[str, Any]) -> dict[str, str]:
    values: dict[str, str] = {}
    core_fields = [
        "so_van_ban",
        "ngay_ban_hanh",
        "co_quan_ban_hanh",
        "loai_van_ban",
        "trich_yeu",
    ]
    for field_name in core_fields:
        field = kie_result.get(field_name) or {}
        value = field.get("value") if isinstance(field, dict) else None
        if isinstance(value, str) and value.strip():
            values[field_name] = value

    custom_fields = kie_result.get("custom_fields") or {}
    if isinstance(custom_fields, dict):
        for field_name, field_data in custom_fields.items():
            value = field_data.get("value") if isinstance(field_data, dict) else None
            if isinstance(value, str) and value.strip():
                values[field_name] = value
    return values


def map_kie_fields_to_bboxes(
    kie_result: dict[str, Any],
    ocr_lines: list[dict[str, Any]],
    *,
    min_match_score: float = 0.55,
) -> dict[str, list[int] | None]:
    """
    Map each extracted KIE field to the best OCR line bounding box.
    """
    field_values = _extract_field_values(kie_result)
    normalized_lines: list[tuple[str, list[int]]] = []
    for line in ocr_lines or []:
        text = str(line.get("text", "") or "")
        bbox = line.get("bbox")
        if not isinstance(bbox, list) or len(bbox) != 4:
            continue
        if not text.strip():
            continue
        normalized_lines.append((_normalize_text(text), [int(v) for v in bbox]))

    mapped: dict[str, list[int] | None] = {}
    for field_name, field_value in field_values.items():
        normalized_value = _normalize_text(field_value)
        best_score = 0.0
        best_bbox: list[int] | None = None
        for line_text, line_bbox in normalized_lines:
            score = _line_match_score(normalized_value, line_text)
            if score > best_score:
                best_score = score
                best_bbox = line_bbox
        mapped[field_name] = best_bbox if best_score >= min_match_score else None
    return mapped
