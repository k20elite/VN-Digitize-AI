from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI, File, Form, HTTPException, UploadFile

from app.schemas import (
    AutoSummaryRequest,
    AutoSummaryResponse,
    OCRAutoSummaryRequest,
    OCRAutoSummaryResponse,
    OCRRequest,
    OCRResponse,
    PreprocessRequest,
    PreprocessResponse,
    ScanUploadResponse,
    ScannerSettings,
    UploadPreprocessResponse,
)
from app.services.barcode_splitter import split_pages_by_barcode
from app.services.ocr import run_ocr_fulltext
from app.services.preprocessing import run_preprocess_pipeline
from app.services.scanner import ScanConfig, scan_from_device
from app.services.summarizer import summarize_with_ollama

app = FastAPI(title="VN-Digitize OCR API", version="0.1.0")

DATA_DIR = Path("data")
RAW_DIR = DATA_DIR / "raw"
PREPROCESSED_DIR = DATA_DIR / "preprocessed"


def _save_uploads(files: list[UploadFile], destination: Path) -> list[Path]:
    destination.mkdir(parents=True, exist_ok=True)
    saved_paths: list[Path] = []
    for file in files:
        suffix = Path(file.filename or "page").suffix or ".png"
        out_path = destination / f"{uuid4().hex}{suffix}"
        with out_path.open("wb") as out:
            out.write(file.file.read())
        saved_paths.append(out_path)
    return saved_paths


@app.post("/api/v1/scan-upload", response_model=ScanUploadResponse)
def scan_or_upload(
    source: str = Form(..., description="scanner or upload"),
    dpi: int = Form(300),
    color_mode: str = Form("color"),
    files: list[UploadFile] = File(default_factory=list),
) -> ScanUploadResponse:
    if source not in {"scanner", "upload"}:
        raise HTTPException(status_code=400, detail="source must be scanner or upload")

    session_dir = RAW_DIR / uuid4().hex
    session_dir.mkdir(parents=True, exist_ok=True)

    if source == "scanner":
        try:
            settings = ScannerSettings(dpi=dpi, color_mode=color_mode)
            page_paths = scan_from_device(
                session_dir, ScanConfig(dpi=settings.dpi, color_mode=settings.color_mode)
            )
        except NotImplementedError as exc:
            raise HTTPException(status_code=501, detail=str(exc)) from exc
        except Exception as exc:  # pragma: no cover
            raise HTTPException(status_code=500, detail=f"scanner error: {exc}") from exc
    else:
        if not files:
            raise HTTPException(status_code=400, detail="files are required for upload")
        page_paths = _save_uploads(files, session_dir)

    if not page_paths:
        raise HTTPException(status_code=400, detail="no pages available after input")

    try:
        bundles = split_pages_by_barcode(page_paths)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return ScanUploadResponse(
        source=source,
        total_pages=len(page_paths),
        bundles=bundles,
        saved_pages=[str(path) for path in page_paths],
    )


@app.post("/api/v1/preprocess", response_model=PreprocessResponse)
def preprocess(request: PreprocessRequest) -> PreprocessResponse:
    output_dir = PREPROCESSED_DIR / uuid4().hex
    try:
        results = run_preprocess_pipeline(request.input_paths, output_dir, request.options)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    total_outputs = sum(1 for item in results if not item["skipped_as_blank"])
    return PreprocessResponse(
        total_inputs=len(request.input_paths),
        total_outputs=total_outputs,
        results=results,
    )


@app.post("/api/v1/upload-preprocess", response_model=UploadPreprocessResponse)
def upload_and_preprocess(
    files: list[UploadFile] = File(default_factory=list),
    deskew: bool = Form(True),
    auto_crop: bool = Form(True),
    shadow_removal: bool = Form(True),
    denoise: bool = Form(True),
    remove_yellow_stains: bool = Form(True),
    binarize: bool = Form(False),
    preserve_red_stamp: bool = Form(True),
    remove_blank_pages: bool = Form(True),
    blank_ratio_threshold: float = Form(0.006),
) -> UploadPreprocessResponse:
    if not files:
        raise HTTPException(status_code=400, detail="files are required")

    raw_dir = RAW_DIR / uuid4().hex
    saved_paths = _save_uploads(files, raw_dir)

    preprocess_request = PreprocessRequest(
        input_paths=[str(path) for path in saved_paths],
        options={
            "deskew": deskew,
            "auto_crop": auto_crop,
            "shadow_removal": shadow_removal,
            "denoise": denoise,
            "remove_yellow_stains": remove_yellow_stains,
            "binarize": binarize,
            "preserve_red_stamp": preserve_red_stamp,
            "remove_blank_pages": remove_blank_pages,
            "blank_ratio_threshold": blank_ratio_threshold,
        },
    )

    output_dir = PREPROCESSED_DIR / uuid4().hex
    try:
        results = run_preprocess_pipeline(
            preprocess_request.input_paths,
            output_dir,
            preprocess_request.options,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    total_outputs = sum(1 for item in results if not item["skipped_as_blank"])
    return UploadPreprocessResponse(
        total_uploaded=len(saved_paths),
        total_outputs=total_outputs,
        saved_pages=[str(path) for path in saved_paths],
        results=results,
    )


@app.post("/api/v1/ocr-fulltext", response_model=OCRResponse)
def ocr_fulltext(request: OCRRequest) -> OCRResponse:
    try:
        result = run_ocr_fulltext(
            input_paths=request.input_paths,
            lang=request.lang,
            psm=request.psm,
            oem=request.oem,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return OCRResponse(**result)


@app.post("/api/v1/auto-summary", response_model=AutoSummaryResponse)
def auto_summary(request: AutoSummaryRequest) -> AutoSummaryResponse:
    try:
        result = summarize_with_ollama(
            text=request.text,
            model=request.model,
            ollama_url=request.ollama_url,
            max_words=request.max_words,
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return AutoSummaryResponse(**result)


@app.post("/api/v1/ocr-auto-summary", response_model=OCRAutoSummaryResponse)
def ocr_auto_summary(request: OCRAutoSummaryRequest) -> OCRAutoSummaryResponse:
    try:
        ocr_result = run_ocr_fulltext(
            input_paths=request.input_paths,
            lang=request.lang,
            psm=request.psm,
            oem=request.oem,
        )
        merged_text = "\n\n".join(
            page["full_text"] for page in ocr_result["pages"] if page["full_text"]
        ).strip()
        if not merged_text:
            raise ValueError("OCR produced empty text; cannot generate summary.")
        summary_result = summarize_with_ollama(
            text=merged_text,
            model=request.model,
            ollama_url=request.ollama_url,
            max_words=request.max_words,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    return OCRAutoSummaryResponse(
        ocr=OCRResponse(**ocr_result),
        summary=summary_result["summary"],
        model=summary_result["model"],
    )
