from __future__ import annotations

import logging
from typing import Any

from paddleocr import PaddleOCR

# Configure logger
logger = logging.getLogger(__name__)

# Global predictor instance to optimize batch processing and avoid reloading model
_PADDLE_OCR_PREDICTOR = None

def get_paddleocr_predictor(lang: str = "vi", use_angle_cls: bool = True) -> PaddleOCR:
    """
    Initialize and return the PaddleOCR singleton instance.
    Optimized for batch processing by caching the predictor in memory.
    """
    global _PADDLE_OCR_PREDICTOR
    if _PADDLE_OCR_PREDICTOR is None:
        logger.info(f"Initializing PaddleOCR with lang='{lang}', use_angle_cls={use_angle_cls}...")
        _PADDLE_OCR_PREDICTOR = PaddleOCR(use_angle_cls=use_angle_cls, lang=lang, show_log=False)
    return _PADDLE_OCR_PREDICTOR

def normalize_bbox(polygon: list[list[float]]) -> list[int]:
    """
    Convert PaddleOCR 4-point polygon to [x, y, w, h] bounding box.
    Input format: [[x1, y1], [x2, y2], [x3, y3], [x4, y4]]
    """
    xs = [pt[0] for pt in polygon]
    ys = [pt[1] for pt in polygon]
    
    x_min, x_max = min(xs), max(xs)
    y_min, y_max = min(ys), max(ys)
    
    return [int(x_min), int(y_min), int(x_max - x_min), int(y_max - y_min)]

def run_ocr_fulltext(
    input_paths: list[str], lang: str = "vi", psm: int = 6, oem: int = 3
) -> dict[str, Any]:
    """
    Extracts text and bounding boxes from a list of image paths using PaddleOCR.
    Handles Vietnamese text, multi-line, preserves bounding boxes accurately, 
    and returns them normalized as [x, y, w, h].
    
    (Note: psm and oem parameters are kept for API signature compatibility with 
    the previous Tesseract implementation, but are ignored by PaddleOCR).
    """
    # Map legacy Tesseract 'vie' to PaddleOCR 'vi'
    if lang == "vie":
        lang = "vi"
        
    predictor = get_paddleocr_predictor(lang=lang, use_angle_cls=True)
    
    pages: list[dict[str, Any]] = []
    
    for input_path in input_paths:
        try:
            # result structure for single image is a list containing line items
            # We enforce cls=True to do angle classification per user requirements
            result = predictor.ocr(input_path, cls=True)
        except Exception as e:
            logger.error(f"Error processing {input_path} with PaddleOCR: {e}")
            raise RuntimeError(f"OCR failed for {input_path}") from e

        lines: list[dict[str, Any]] = []
        full_text_parts: list[str] = []
        
        # result can be None if no text is found, or a list containing None
        if result and result[0]:
            for line in result[0]:
                poly_box = line[0]        # e.g. [[43.0, 31.0], [339.0, 33.0], ...]
                text = line[1][0]         # text content
                confidence = float(line[1][1])   # confidence score

                bbox = normalize_bbox(poly_box)

                lines.append({
                    "text": text,
                    "bbox": bbox,
                    "confidence": confidence
                })
                full_text_parts.append(text)
                
        full_text = "\n".join(full_text_parts)

        pages.append({
            "input_path": input_path,
            "full_text": full_text,
            "lines": lines
        })

    return {
        "total_pages": len(pages),
        "pages": pages
    }
