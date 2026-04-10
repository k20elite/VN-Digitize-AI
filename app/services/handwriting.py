from __future__ import annotations

from pathlib import Path
from typing import Any

import cv2
import numpy as np

_TROCR_PROCESSOR = None
_TROCR_MODEL = None
_TROCR_FAILED = False


def _get_trocr_components():
    global _TROCR_PROCESSOR, _TROCR_MODEL, _TROCR_FAILED
    if _TROCR_FAILED:
        return None, None
    if _TROCR_PROCESSOR is not None and _TROCR_MODEL is not None:
        return _TROCR_PROCESSOR, _TROCR_MODEL
    try:
        from transformers import TrOCRProcessor, VisionEncoderDecoderModel
    except Exception:
        _TROCR_FAILED = True
        return None, None

    try:
        _TROCR_PROCESSOR = TrOCRProcessor.from_pretrained("microsoft/trocr-base-handwritten")
        _TROCR_MODEL = VisionEncoderDecoderModel.from_pretrained("microsoft/trocr-base-handwritten")
    except Exception:
        _TROCR_FAILED = True
        return None, None
    return _TROCR_PROCESSOR, _TROCR_MODEL


def _refine_line_with_trocr(
    image_bgr: np.ndarray,
    line: dict[str, Any],
    processor: Any,
    model: Any,
) -> dict[str, Any]:
    bbox = line.get("bbox") or []
    if len(bbox) != 4:
        return line
    x, y, w, h = [int(v) for v in bbox]
    if w <= 0 or h <= 0:
        return line
    y2 = min(image_bgr.shape[0], y + h)
    x2 = min(image_bgr.shape[1], x + w)
    crop = image_bgr[max(0, y):y2, max(0, x):x2]
    if crop.size == 0:
        return line
    try:
        from PIL import Image
    except Exception:
        return line
    crop_rgb = cv2.cvtColor(crop, cv2.COLOR_BGR2RGB)
    try:
        pixel_values = processor(images=Image.fromarray(crop_rgb), return_tensors="pt").pixel_values
        generated_ids = model.generate(pixel_values)
        text = processor.batch_decode(generated_ids, skip_special_tokens=True)[0].strip()
    except Exception:
        return line
    if not text:
        return line
    refined = dict(line)
    refined["text"] = text
    refined["confidence"] = max(float(line.get("confidence", 0.0)), 80.0)
    return refined


def refine_ocr_for_handwriting(
    pages: list[dict[str, Any]],
    *,
    low_confidence_threshold: float = 70.0,
) -> dict[str, Any]:
    processor, model = _get_trocr_components()
    if processor is None or model is None:
        return {
            "applied": False,
            "reason": "handwriting model unavailable",
            "pages": pages,
        }

    refined_pages: list[dict[str, Any]] = []
    for page in pages:
        input_path = str(page.get("input_path", ""))
        image = cv2.imread(input_path) if input_path else None
        if image is None:
            refined_pages.append(page)
            continue
        updated_lines: list[dict[str, Any]] = []
        for line in page.get("lines", []):
            conf = float(line.get("confidence", 0.0))
            if conf <= low_confidence_threshold:
                updated_lines.append(_refine_line_with_trocr(image, line, processor, model))
            else:
                updated_lines.append(line)
        updated_page = dict(page)
        updated_page["lines"] = updated_lines
        updated_page["full_text"] = "\n".join(
            str(item.get("text", "")).strip() for item in updated_lines if str(item.get("text", "")).strip()
        ).strip()
        refined_pages.append(updated_page)

    return {"applied": True, "reason": None, "pages": refined_pages}
