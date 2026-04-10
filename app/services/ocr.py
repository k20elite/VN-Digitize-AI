from __future__ import annotations

<<<<<<< HEAD
import sys
import threading
from pathlib import Path
from typing import Any

import cv2

_DEEPOCR_ENGINE = None
_DEEPOCR_LOCK = threading.Lock()


def _resolve_deepdoc_root() -> Path:
    project_root = Path(__file__).resolve().parents[2]
    candidates = [
        project_root / "deepdoc_vietocr",
        project_root / "external" / "deepdoc_vietocr",
        project_root / "external" / "deepdoc_vietocr_repo",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    raise RuntimeError(
        "Cannot find deepdoc_vietocr source folder. Expected one of: "
        "deepdoc_vietocr/, external/deepdoc_vietocr/, external/deepdoc_vietocr_repo/."
    )


def _get_deepdoc_engine():
    global _DEEPOCR_ENGINE
    if _DEEPOCR_ENGINE is not None:
        return _DEEPOCR_ENGINE

    with _DEEPOCR_LOCK:
        if _DEEPOCR_ENGINE is not None:
            return _DEEPOCR_ENGINE

        deepdoc_root = _resolve_deepdoc_root()
        # deepdoc module uses absolute imports like "from utils.file_utils ...".
        # We add both the project root (for `deepdoc_vietocr.module.*` import style)
        # and the deepdoc root itself (for `module.*` / `utils.*` absolute imports).
        deepdoc_root_str = str(deepdoc_root)
        deepdoc_parent_str = str(deepdoc_root.parent)
        if deepdoc_parent_str not in sys.path:
            sys.path.insert(0, deepdoc_parent_str)
        if deepdoc_root_str not in sys.path:
            sys.path.insert(0, deepdoc_root_str)

        try:
            try:
                from deepdoc_vietocr.module.ocr import OCR as DeepDocOCR
            except ModuleNotFoundError as exc:
                if (exc.name or "") != "deepdoc_vietocr.module":
                    raise
                # Fallback when deepdoc root is present but package-style import
                # cannot be resolved (common in local source checkout layout).
                from module.ocr import OCR as DeepDocOCR  # type: ignore
        except ModuleNotFoundError as exc:
            missing = exc.name or "unknown"
            raise RuntimeError(
                "Failed to import deepdoc_vietocr OCR due to missing dependency "
                f"`{missing}`. Install project requirements with: pip install -r requirements.txt"
            ) from exc
        except Exception as exc:
            raise RuntimeError(
                "Failed to import deepdoc_vietocr OCR. Install required deps first "
                "(for example: pdfplumber, onnxruntime, huggingface-hub, ruamel.yaml, "
                "cachetools, pycryptodomex, strenum)."
            ) from exc

        try:
            _DEEPOCR_ENGINE = DeepDocOCR()
        except Exception as exc:
            raise RuntimeError(f"Failed to initialize deepdoc_vietocr OCR: {exc}") from exc
        return _DEEPOCR_ENGINE


def _quad_to_bbox(points: list[list[float]]) -> list[int]:
    if not points:
        return [0, 0, 0, 0]
    xs = [int(round(point[0])) for point in points]
    ys = [int(round(point[1])) for point in points]
    left, right = min(xs), max(xs)
    top, bottom = min(ys), max(ys)
    return [left, top, max(0, right - left), max(0, bottom - top)]


def _normalize_deepdoc_result(raw_items: Any) -> list[dict]:
    lines: list[dict] = []
    if not raw_items:
        return lines

    for item in raw_items:
        if not item or len(item) != 2:
            continue
        points, recognition = item
        if not recognition or len(recognition) != 2:
            continue

        text, score = recognition
        cleaned_text = (text or "").strip()
        if not cleaned_text:
            continue

        confidence = float(score)
        if confidence <= 1.0:
            confidence *= 100.0

        lines.append(
            {
                "text": cleaned_text,
                "bbox": _quad_to_bbox(points),
                "confidence": confidence,
=======
import shutil
import subprocess
from pathlib import Path

import cv2
from PIL import Image


_VIETOCR_PREDICTOR = None


def _resolve_tesseract_cmd() -> str:
    candidate = shutil.which("tesseract")
    if candidate:
        return candidate
    windows_default = Path("C:/Program Files/Tesseract-OCR/tesseract.exe")
    if windows_default.exists():
        return str(windows_default)
    raise RuntimeError(
        "Tesseract is not available in PATH and default install path was not found."
    )


def _run_tesseract_tsv(image_path: str, lang: str, psm: int, oem: int) -> str:
    input_path = Path(image_path)
    if not input_path.exists():
        raise ValueError(f"Input image does not exist: {image_path}")

    tesseract_cmd = _resolve_tesseract_cmd()
    process = subprocess.run(
        [
            tesseract_cmd,
            str(input_path),
            "stdout",
            "-l",
            lang,
            "--psm",
            str(psm),
            "--oem",
            str(oem),
            "tsv",
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    if process.returncode != 0:
        message = process.stderr.strip() or process.stdout.strip() or "Unknown OCR error"
        raise RuntimeError(f"Tesseract OCR failed for {image_path}: {message}")
    return process.stdout


def _get_vietocr_predictor():
    global _VIETOCR_PREDICTOR
    if _VIETOCR_PREDICTOR is not None:
        return _VIETOCR_PREDICTOR

    try:
        from vietocr.tool.config import Cfg
        from vietocr.tool.predictor import Predictor
    except Exception as exc:
        raise RuntimeError(
            "VietOCR is not available. Install with: pip install vietocr"
        ) from exc

    config = Cfg.load_config_from_name("vgg_transformer")
    config["weights"] = "https://vocr.vn/vietocr/weights/vgg_transformer.pth"
    config["weights"] = "https://vocr.vn/vietocr/weights/vgg_transformer.pth"
    config["weights"] = "https://vocr.vn/vietocr/weights/vgg_transformer.pth"
    config["weights"] = "https://vocr.vn/vietocr/weights/vgg_transformer.pth"
    config["weights"] = "https://vocr.vn/vietocr/weights/vgg_transformer.pth"
    config["weights"] = "https://vocr.vn/vietocr/weights/vgg_transformer.pth"
    config["weights"] = "https://vocr.vn/vietocr/weights/vgg_transformer.pth"
    config["weights"] = "https://vocr.vn/vietocr/weights/vgg_transformer.pth"
    config["weights"] = "https://vocr.vn/vietocr/weights/vgg_transformer.pth"
    config["weights"] = "https://vocr.vn/vietocr/weights/vgg_transformer.pth"
    config["device"] = "cpu"
    _VIETOCR_PREDICTOR = Predictor(config)
    return _VIETOCR_PREDICTOR


def _apply_vietocr_recognition(image_bgr, lines: list[dict]) -> list[dict]:
    predictor = _get_vietocr_predictor()
    h, w = image_bgr.shape[:2]
    recognized_lines: list[dict] = []

    for line in lines:
        x, y, bw, bh = line["bbox"]
        if bw <= 0 or bh <= 0:
            recognized_lines.append(line)
            continue

        pad_x = max(1, int(0.02 * bw))
        pad_y = max(1, int(0.25 * bh))
        x0 = max(0, x - pad_x)
        y0 = max(0, y - pad_y)
        x1 = min(w, x + bw + pad_x)
        y1 = min(h, y + bh + pad_y)
        crop = image_bgr[y0:y1, x0:x1]
        if crop.size == 0:
            recognized_lines.append(line)
            continue

        pil_image = Image.fromarray(cv2.cvtColor(crop, cv2.COLOR_BGR2RGB))
        predicted_text = (predictor.predict(pil_image) or "").strip()

        if predicted_text:
            updated = dict(line)
            updated["text"] = predicted_text
            recognized_lines.append(updated)
        else:
            recognized_lines.append(line)

    return recognized_lines


def _parse_tesseract_tsv(tsv_content: str) -> list[dict]:
    raw_lines = tsv_content.splitlines()
    if not raw_lines:
        return []

    headers = raw_lines[0].split("\t")
    expected_columns = 12
    if len(headers) < expected_columns:
        return []

    line_buckets: dict[tuple[int, int, int, int], dict] = {}

    for raw_line in raw_lines[1:]:
        if not raw_line.strip():
            continue

        # Keep the OCR "text" column intact even if it contains tabs.
        columns = raw_line.split("\t", expected_columns - 1)
        if len(columns) != expected_columns:
            continue
        row = dict(zip(headers[:expected_columns], columns))

        text = (row.get("text") or "").strip()
        level_str = (row.get("level") or "0").strip()
        if not level_str.isdigit():
            continue
        level = int(level_str)
        if level != 5 or not text:
            continue

        try:
            left = int((row.get("left") or "0").strip())
            top = int((row.get("top") or "0").strip())
            width = int((row.get("width") or "0").strip())
            height = int((row.get("height") or "0").strip())
            conf = float((row.get("conf") or "-1").strip())
            page_num = int((row.get("page_num") or "1").strip())
            block_num = int((row.get("block_num") or "0").strip())
            par_num = int((row.get("par_num") or "0").strip())
            line_num = int((row.get("line_num") or "0").strip())
        except ValueError:
            continue

        if width <= 0 or height <= 0:
            continue

        key = (
            page_num,
            block_num,
            par_num,
            line_num,
        )
        bucket = line_buckets.get(key)
        if bucket is None:
            line_buckets[key] = {
                "parts": [text],
                "left": left,
                "top": top,
                "right": left + width,
                "bottom": top + height,
                "conf_sum": max(conf, 0.0),
                "conf_count": 1 if conf >= 0 else 0,
            }
            continue

        bucket["parts"].append(text)
        bucket["left"] = min(bucket["left"], left)
        bucket["top"] = min(bucket["top"], top)
        bucket["right"] = max(bucket["right"], left + width)
        bucket["bottom"] = max(bucket["bottom"], top + height)
        if conf >= 0:
            bucket["conf_sum"] += conf
            bucket["conf_count"] += 1

    lines: list[dict] = []
    for key in sorted(line_buckets.keys()):
        bucket = line_buckets[key]
        conf_count = bucket["conf_count"]
        confidence = bucket["conf_sum"] / conf_count if conf_count > 0 else 0.0
        lines.append(
            {
                "text": " ".join(bucket["parts"]).strip(),
                "bbox": [
                    int(bucket["left"]),
                    int(bucket["top"]),
                    int(bucket["right"] - bucket["left"]),
                    int(bucket["bottom"] - bucket["top"]),
                ],
                "confidence": float(confidence),
>>>>>>> fa883a38ced3be0325d8d4a97f8c1c11e446b43c
            }
        )
    return lines


def run_ocr_fulltext(
    input_paths: list[str], lang: str = "vie", psm: int = 6, oem: int = 3
) -> dict:
<<<<<<< HEAD
    # Keep API compatibility with previous request schema; deepdoc OCR does not use these.
    _ = (lang, psm, oem)

    ocr_engine = _get_deepdoc_engine()
    pages: list[dict] = []

    for input_path in input_paths:
        image_path = Path(input_path)
        if not image_path.exists():
            raise ValueError(f"Input image does not exist: {input_path}")

        image_bgr = cv2.imread(str(image_path))
        if image_bgr is None:
            raise ValueError(f"Cannot read image for OCR: {input_path}")

        try:
            deepdoc_items = ocr_engine(image_bgr)
        except Exception as exc:
            raise RuntimeError(f"deepdoc_vietocr failed for {input_path}: {exc}") from exc

        lines = _normalize_deepdoc_result(deepdoc_items)
        full_text = "\n".join(line["text"] for line in lines).strip()
=======
    pages: list[dict] = []
    for input_path in input_paths:
        image_bgr = cv2.imread(input_path)
        if image_bgr is None:
            raise ValueError(f"Cannot read image for OCR: {input_path}")
        tsv_content = _run_tesseract_tsv(input_path, lang=lang, psm=psm, oem=oem)
        lines = _parse_tesseract_tsv(tsv_content)
        if lines:
            lines = _apply_vietocr_recognition(image_bgr=image_bgr, lines=lines)
        full_text = "\n".join(line["text"] for line in lines if line["text"]).strip()
>>>>>>> fa883a38ced3be0325d8d4a97f8c1c11e446b43c
        pages.append(
            {
                "input_path": input_path,
                "full_text": full_text,
                "lines": lines,
            }
        )

<<<<<<< HEAD
    return {"total_pages": len(pages), "pages": pages}
=======
    return {
        "total_pages": len(pages),
        "pages": pages,
    }
>>>>>>> fa883a38ced3be0325d8d4a97f8c1c11e446b43c
