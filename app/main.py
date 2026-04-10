from __future__ import annotations

from pathlib import Path
<<<<<<< HEAD
import shutil
from uuid import uuid4

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
=======
from uuid import uuid4

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
>>>>>>> fa883a38ced3be0325d8d4a97f8c1c11e446b43c

from app.schemas import (
    AutoSummaryRequest,
    AutoSummaryResponse,
<<<<<<< HEAD
    CustomFieldDef,  # noqa: F401  (re-exported for OpenAPI visibility)
    ExtractFieldsRequest,
    ExtractFieldsResponse,
    KIEField,
    KIERequest,
    KIEResponse,
    KIEResult,
    KIETemplate,    # noqa: F401
    OCRAutoSummaryRequest,
    OCRAutoSummaryResponse,
    OCRKIEPageResult,
    OCRKIERequest,
    OCRKIEResponse,
    PostprocessRequest,
    PostprocessResponse,
=======
    OCRAutoSummaryRequest,
    OCRAutoSummaryResponse,
>>>>>>> fa883a38ced3be0325d8d4a97f8c1c11e446b43c
    OCRRequest,
    OCRResponse,
    PreprocessRequest,
    PreprocessResponse,
    ScanUploadResponse,
    ScannerSettings,
<<<<<<< HEAD
    SplitDocumentRequest,
    SplitDocumentResponse,
    UploadPreprocessResponse,
    ValidationResult,
    AsyncTaskResponse,
    TaskStatusResponse,
    ExportPDFRequest,
    ExportPDFResponse,
    FeedbackRequest,
    FeedbackResponse,
    QA1ReviewCreateRequest,
    QAReviewResponse,
    QA2DecisionRequest,
    QA2DecisionResponse,
    QAFieldFlag,
    SplitViewPayload,
    ArchiveStoreRequest,
    ArchiveStoreResponse,
    IncrementalLearningRetrainRequest,
    IncrementalLearningStatusResponse,
)
from app.services.barcode_splitter import split_pages_by_barcode
from app.services.document_splitter import split_document_by_content
from app.services.kie_extractor import extract_kie, extract_kie_from_pages
from app.services.ocr import run_ocr_fulltext
from app.services.postprocessing import run_postprocess_pipeline
from app.services.preprocessing import run_preprocess_pipeline
from app.services.pdf_exporter import export_searchable_pdf
from app.services.feedback import save_feedback
from app.services.kie_field_bbox import map_kie_fields_to_bboxes
from app.services.qa_workflow import create_qa_session, get_qa_session, update_qa_session
from app.services.handwriting import refine_ocr_for_handwriting
from app.services.incremental_learning import (
    retrain_incremental_from_feedback,
    DEFAULT_LEXICON_PATH,
    get_incremental_status,
)
from app.services.nlp_correction import correct_text_nlp
from app.services.scanner import ScanConfig, scan_from_device
from app.services.summarizer import summarize_with_ollama
from app.services.validation import validate_document_logic
from app.celery_app import celery_app
from app.tasks import process_ocr_kie, process_split_document
from app.ui_router import router as ui_router

app = FastAPI(title="VN-Digitize OCR API", version="0.1.0")
app.include_router(ui_router)
=======
    UploadPreprocessResponse,
)
from app.services.barcode_splitter import split_pages_by_barcode
from app.services.ocr import run_ocr_fulltext
from app.services.preprocessing import run_preprocess_pipeline
from app.services.scanner import ScanConfig, scan_from_device
from app.services.summarizer import summarize_with_ollama

app = FastAPI(title="VN-Digitize OCR API", version="0.1.0")
>>>>>>> fa883a38ced3be0325d8d4a97f8c1c11e446b43c

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


<<<<<<< HEAD
def _to_kie_result(raw: dict) -> KIEResult:
    field_bboxes = raw.get("field_bboxes", {}) if isinstance(raw, dict) else {}
    raw_custom = raw.get("custom_fields", {})
    custom_kie = {
        k: KIEField(
            value=v.get("value"),
            confidence=v.get("confidence", 0.0),
            field_bbox=field_bboxes.get(k),
        )
        for k, v in raw_custom.items()
    }
    return KIEResult(
        so_van_ban=KIEField(
            value=raw["so_van_ban"].get("value"),
            confidence=raw["so_van_ban"].get("confidence", 0.0),
            field_bbox=field_bboxes.get("so_van_ban"),
        ),
        ngay_ban_hanh=KIEField(
            value=raw["ngay_ban_hanh"].get("value"),
            confidence=raw["ngay_ban_hanh"].get("confidence", 0.0),
            field_bbox=field_bboxes.get("ngay_ban_hanh"),
        ),
        co_quan_ban_hanh=KIEField(
            value=raw["co_quan_ban_hanh"].get("value"),
            confidence=raw["co_quan_ban_hanh"].get("confidence", 0.0),
            field_bbox=field_bboxes.get("co_quan_ban_hanh"),
        ),
        loai_van_ban=KIEField(
            value=raw["loai_van_ban"].get("value"),
            confidence=raw["loai_van_ban"].get("confidence", 0.0),
            field_bbox=field_bboxes.get("loai_van_ban"),
        ),
        trich_yeu=KIEField(
            value=raw["trich_yeu"].get("value"),
            confidence=raw["trich_yeu"].get("confidence", 0.0),
            field_bbox=field_bboxes.get("trich_yeu"),
        ),
        custom_fields=custom_kie,
        model_used=raw.get("model_used"),
    )


def _attach_field_bboxes(kie_raw: dict, lines: list[dict]) -> dict:
    field_bboxes = map_kie_fields_to_bboxes(kie_raw, lines)
    enriched = dict(kie_raw)
    enriched["field_bboxes"] = field_bboxes
    return enriched


def _iter_all_fields(document: KIEResult) -> list[tuple[str, KIEField]]:
    fields = [
        ("so_van_ban", document.so_van_ban),
        ("ngay_ban_hanh", document.ngay_ban_hanh),
        ("co_quan_ban_hanh", document.co_quan_ban_hanh),
        ("loai_van_ban", document.loai_van_ban),
        ("trich_yeu", document.trich_yeu),
    ]
    for key, item in document.custom_fields.items():
        fields.append((key, item))
    return fields


def _build_low_confidence_flags(
    document: KIEResult,
    *,
    red_threshold: float,
    yellow_threshold: float,
) -> list[QAFieldFlag]:
    flags: list[QAFieldFlag] = []
    for field_name, item in _iter_all_fields(document):
        conf = float(item.confidence or 0.0)
        if conf < red_threshold:
            flags.append(
                QAFieldFlag(
                    field_name=field_name,
                    value=item.value,
                    confidence=conf,
                    field_bbox=item.field_bbox,
                    highlight_color="red",
                )
            )
        elif conf < yellow_threshold:
            flags.append(
                QAFieldFlag(
                    field_name=field_name,
                    value=item.value,
                    confidence=conf,
                    field_bbox=item.field_bbox,
                    highlight_color="yellow",
                )
            )
    return flags


def _maybe_refine_handwriting(
    ocr_result: dict,
    *,
    enabled: bool,
) -> dict:
    if not enabled:
        return ocr_result
    refined = refine_ocr_for_handwriting(ocr_result.get("pages", []))
    result = dict(ocr_result)
    result["pages"] = refined.get("pages", ocr_result.get("pages", []))
    return result


=======
>>>>>>> fa883a38ced3be0325d8d4a97f8c1c11e446b43c
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
<<<<<<< HEAD
        result = _maybe_refine_handwriting(result, enabled=request.handwriting_support)
=======
>>>>>>> fa883a38ced3be0325d8d4a97f8c1c11e446b43c
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
<<<<<<< HEAD
        ocr_result = _maybe_refine_handwriting(ocr_result, enabled=request.handwriting_support)
=======
>>>>>>> fa883a38ced3be0325d8d4a97f8c1c11e446b43c
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
<<<<<<< HEAD


@app.post("/api/v1/kie", response_model=KIEResponse)
def kie_extract(request: KIERequest) -> KIEResponse:
    """
    Extract structured key information from raw OCR text of a Vietnamese
    administrative / legal document.

    Uses a hybrid approach:
    - Stage 1: regex / pattern matching (fast, deterministic)
    - Stage 2: LLM via Ollama (optional, contextual; skipped on error/timeout)

    Optionally accepts a ``template`` with ``custom_fields`` to extract
    domain-specific fields beyond the 5 standard ones (e.g. for courts or
    insurance agencies).
    """
    merged = extract_kie(
        text=request.text,
        model=request.model,
        ollama_url=request.ollama_url,
        use_llm=request.use_llm,
        template=request.template,
    )
    # Map raw custom_fields dict -> dict[str, KIEField]
    raw_custom = merged.get("custom_fields", {})
    custom_kie = {k: KIEField(**v) for k, v in raw_custom.items()}
    result = KIEResult(
        so_van_ban=merged["so_van_ban"],
        ngay_ban_hanh=merged["ngay_ban_hanh"],
        co_quan_ban_hanh=merged["co_quan_ban_hanh"],
        loai_van_ban=merged["loai_van_ban"],
        trich_yeu=merged["trich_yeu"],
        custom_fields=custom_kie,
        model_used=merged.get("model_used"),
    )
    return KIEResponse(result=result)


@app.post("/api/v1/ocr-kie", response_model=OCRKIEResponse)
def ocr_kie(request: OCRKIERequest) -> OCRKIEResponse:
    """
    Full pipeline: images → OCR → KIE.

    Response contains:
    - ``pages``    : per-page OCR text + bounding-box lines + KIE fields
                     (for UI highlighting, QA, and debugging)
    - ``document`` : document-level KIE merged from all pages
                     (highest-confidence value per field; for business use)

    Optionally accepts a ``template`` with ``custom_fields`` for domain-specific
    extraction on top of the 5 standard administrative fields.
    """
    try:
        ocr_result = run_ocr_fulltext(
            input_paths=request.input_paths,
            lang=request.lang,
            psm=request.psm,
            oem=request.oem,
        )
        ocr_result = _maybe_refine_handwriting(ocr_result, enabled=request.handwriting_support)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    ocr_pages = ocr_result["pages"]  # list of dicts with input_path/full_text/lines

    kie_result = extract_kie_from_pages(
        ocr_pages=ocr_pages,
        model=request.model,
        ollama_url=request.ollama_url,
        use_llm=request.use_llm,
        template=request.template,
    )

    # Build per-page schema objects (include bbox lines from OCR)
    page_schemas: list[OCRKIEPageResult] = []
    for ocr_page, kie_page in zip(ocr_pages, kie_result["pages"]):
        page_kie_with_bbox = _attach_field_bboxes(kie_page["kie"], ocr_page["lines"])
        page_schemas.append(
            OCRKIEPageResult(
                input_path=ocr_page["input_path"],
                full_text=ocr_page["full_text"],
                lines=ocr_page["lines"],
                kie=_to_kie_result(page_kie_with_bbox),
            )
        )

    document_with_bbox = dict(kie_result["document"])
    if page_schemas:
        first_page_fields = page_schemas[0].kie
        merged_field_bboxes = {
            "so_van_ban": first_page_fields.so_van_ban.field_bbox,
            "ngay_ban_hanh": first_page_fields.ngay_ban_hanh.field_bbox,
            "co_quan_ban_hanh": first_page_fields.co_quan_ban_hanh.field_bbox,
            "loai_van_ban": first_page_fields.loai_van_ban.field_bbox,
            "trich_yeu": first_page_fields.trich_yeu.field_bbox,
        }
        for key, field in first_page_fields.custom_fields.items():
            merged_field_bboxes[key] = field.field_bbox
        document_with_bbox["field_bboxes"] = merged_field_bboxes

    return OCRKIEResponse(
        pages=page_schemas,
        document=_to_kie_result(document_with_bbox),
    )


@app.post("/api/v1/extract-fields", response_model=ExtractFieldsResponse)
def extract_fields(request: ExtractFieldsRequest) -> ExtractFieldsResponse:
    """
    Business endpoint: images -> OCR -> KIE -> logical validation.
    """
    try:
        ocr_result = run_ocr_fulltext(
            input_paths=request.input_paths,
            lang=request.lang,
            psm=request.psm,
            oem=request.oem,
        )
        ocr_result = _maybe_refine_handwriting(ocr_result, enabled=request.handwriting_support)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    ocr_pages = ocr_result["pages"]
    kie_result = extract_kie_from_pages(
        ocr_pages=ocr_pages,
        model=request.model,
        ollama_url=request.ollama_url,
        use_llm=request.use_llm,
        template=request.template,
    )

    page_schemas: list[OCRKIEPageResult] = []
    for ocr_page, kie_page in zip(ocr_pages, kie_result["pages"]):
        page_kie_with_bbox = _attach_field_bboxes(kie_page["kie"], ocr_page["lines"])
        page_schemas.append(
            OCRKIEPageResult(
                input_path=ocr_page["input_path"],
                full_text=ocr_page["full_text"],
                lines=ocr_page["lines"],
                kie=_to_kie_result(page_kie_with_bbox),
            )
        )

    validation = validate_document_logic(kie_result["document"])
    document_with_bbox = dict(kie_result["document"])
    if page_schemas:
        first_page_fields = page_schemas[0].kie
        merged_field_bboxes = {
            "so_van_ban": first_page_fields.so_van_ban.field_bbox,
            "ngay_ban_hanh": first_page_fields.ngay_ban_hanh.field_bbox,
            "co_quan_ban_hanh": first_page_fields.co_quan_ban_hanh.field_bbox,
            "loai_van_ban": first_page_fields.loai_van_ban.field_bbox,
            "trich_yeu": first_page_fields.trich_yeu.field_bbox,
        }
        for key, field in first_page_fields.custom_fields.items():
            merged_field_bboxes[key] = field.field_bbox
        document_with_bbox["field_bboxes"] = merged_field_bboxes

    return ExtractFieldsResponse(
        pages=page_schemas,
        document=_to_kie_result(document_with_bbox),
        validation=ValidationResult(**validation),
    )


@app.post("/api/v1/split-document", response_model=SplitDocumentResponse)
def split_document(request: SplitDocumentRequest) -> SplitDocumentResponse:
    """
    Split a large input into logical documents based on OCR+KIE content signals.
    """
    try:
        ocr_result = run_ocr_fulltext(
            input_paths=request.input_paths,
            lang=request.lang,
            psm=request.psm,
            oem=request.oem,
        )
        ocr_result = _maybe_refine_handwriting(ocr_result, enabled=request.handwriting_support)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    split_result = split_document_by_content(
        ocr_pages=ocr_result["pages"],
        model=request.model,
        ollama_url=request.ollama_url,
        use_llm=request.use_llm,
        template=request.template,
    )
    # Convert nested classification payloads to schema
    for doc in split_result["documents"]:
        doc["classification"] = _to_kie_result(
            _attach_field_bboxes(doc["classification"], [])
        )
    return SplitDocumentResponse(**split_result)


@app.post("/api/v1/postprocess-check", response_model=PostprocessResponse)
def postprocess_check(request: PostprocessRequest) -> PostprocessResponse:
    """
    Post-processing checks: stamp/signature detection and table extraction.
    """
    try:
        ocr_result = run_ocr_fulltext(
            input_paths=request.input_paths,
            lang=request.lang,
            psm=request.psm,
            oem=request.oem,
        )
        ocr_result = _maybe_refine_handwriting(ocr_result, enabled=request.handwriting_support)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    result = run_postprocess_pipeline(
        ocr_pages=ocr_result["pages"],
        yolo_model_path=request.yolo_model_path,
        conf_threshold=request.conf_threshold,
    )
    return PostprocessResponse(**result)


@app.post("/api/v1/async/ocr-kie", response_model=AsyncTaskResponse)
def async_ocr_kie(request: OCRKIERequest) -> AsyncTaskResponse:
    """
    Trigger async OCR -> KIE pipeline.
    """
    task = process_ocr_kie.delay(request.model_dump())
    return AsyncTaskResponse(
        task_id=task.id,
        status="PENDING",
        message="Task submitted successfully."
    )


@app.post("/api/v1/async/split-document", response_model=AsyncTaskResponse)
def async_split_document(request: SplitDocumentRequest) -> AsyncTaskResponse:
    """
    Trigger async document splitting pipeline.
    """
    task = process_split_document.delay(request.model_dump())
    return AsyncTaskResponse(
        task_id=task.id,
        status="PENDING",
        message="Task submitted successfully."
    )


@app.get("/api/v1/task/{task_id}", response_model=TaskStatusResponse)
def get_task_status(task_id: str) -> TaskStatusResponse:
    """
    Check status of an async celery task.
    """
    task_result = celery_app.AsyncResult(task_id)
    result = None
    meta = None
    status = task_result.status
    
    if task_result.state == "SUCCESS":
        result = task_result.result
    elif task_result.state == "FAILURE":
        meta = {"error": str(task_result.result)}
    elif task_result.state == "PROGRESS":
        meta = task_result.info
    
    return TaskStatusResponse(
        task_id=task_id,
        status=status,
        result=result,
        meta=meta
    )


@app.post("/api/v1/export-pdf-searchable", response_model=ExportPDFResponse)
def export_pdf_searchable(request: ExportPDFRequest) -> ExportPDFResponse:
    """
    Exports processing results into a 2-layer PDF/A-like document.
    """
    if not request.pages:
        raise HTTPException(status_code=400, detail="No pages provided to export.")
    
    # Dump the Pydantic models to a dict structure for the service
    pages_data = [page.model_dump() for page in request.pages]
    
    output_dir = DATA_DIR / "exported"
    output_dir.mkdir(parents=True, exist_ok=True)
    out_path = output_dir / request.output_filename

    try:
        export_result = export_searchable_pdf(
            pages_data=pages_data,
            output_path=str(out_path),
            pdfa_level=request.pdfa_level,
            mrc_compression=request.mrc_compression,
            strict_pdfa=request.strict_pdfa,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to create PDF: {exc}") from exc

    return ExportPDFResponse(
        output_path=export_result["output_path"],
        download_url=f"/api/v1/downloads/{Path(export_result['output_path']).name}",
        pdfa_compliant=bool(export_result.get("pdfa_compliant", False)),
        compression=str(export_result.get("compression", "deflate")),
        warnings=list(export_result.get("warnings", [])),
    )


@app.get("/api/v1/downloads/{filename}")
def download_exported_file(filename: str):
    file_path = DATA_DIR / "exported" / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found.")
    return FileResponse(path=file_path, filename=filename, media_type="application/pdf")


@app.post("/api/v1/archive/store", response_model=ArchiveStoreResponse)
def archive_store(request: ArchiveStoreRequest) -> ArchiveStoreResponse:
    source_path = Path(request.input_path)
    if not source_path.exists():
        raise HTTPException(status_code=404, detail="Input file does not exist.")
    archive_dir = DATA_DIR / "archive"
    archive_dir.mkdir(parents=True, exist_ok=True)
    archive_name = f"{request.document_id or uuid4().hex}_{source_path.name}"
    archived_path = archive_dir / archive_name
    shutil.copy2(source_path, archived_path)
    return ArchiveStoreResponse(
        archived_path=str(archived_path),
        document_id=request.document_id,
    )


@app.post("/api/v1/qa1/review-create", response_model=QAReviewResponse)
def qa1_review_create(request: QA1ReviewCreateRequest) -> QAReviewResponse:
    try:
        ocr_result = run_ocr_fulltext(
            input_paths=request.input_paths,
            lang=request.lang,
            psm=request.psm,
            oem=request.oem,
        )
        ocr_result = _maybe_refine_handwriting(ocr_result, enabled=request.handwriting_support)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    ocr_pages = ocr_result["pages"]
    kie_result = extract_kie_from_pages(
        ocr_pages=ocr_pages,
        model=request.model,
        ollama_url=request.ollama_url,
        use_llm=request.use_llm,
        template=request.template,
    )
    page_schemas: list[OCRKIEPageResult] = []
    for ocr_page, kie_page in zip(ocr_pages, kie_result["pages"]):
        page_kie_with_bbox = _attach_field_bboxes(kie_page["kie"], ocr_page["lines"])
        page_schemas.append(
            OCRKIEPageResult(
                input_path=ocr_page["input_path"],
                full_text=ocr_page["full_text"],
                lines=ocr_page["lines"],
                kie=_to_kie_result(page_kie_with_bbox),
            )
        )

    document_with_bbox = dict(kie_result["document"])
    if page_schemas:
        first_page_fields = page_schemas[0].kie
        merged_field_bboxes = {
            "so_van_ban": first_page_fields.so_van_ban.field_bbox,
            "ngay_ban_hanh": first_page_fields.ngay_ban_hanh.field_bbox,
            "co_quan_ban_hanh": first_page_fields.co_quan_ban_hanh.field_bbox,
            "loai_van_ban": first_page_fields.loai_van_ban.field_bbox,
            "trich_yeu": first_page_fields.trich_yeu.field_bbox,
        }
        for key, field in first_page_fields.custom_fields.items():
            merged_field_bboxes[key] = field.field_bbox
        document_with_bbox["field_bboxes"] = merged_field_bboxes

    document_schema = _to_kie_result(document_with_bbox)
    validation = ValidationResult(**validate_document_logic(kie_result["document"]))
    low_confidence_fields = _build_low_confidence_flags(
        document_schema,
        red_threshold=request.red_threshold,
        yellow_threshold=request.yellow_threshold,
    )
    split_view = SplitViewPayload(
        left_image_paths=[page.input_path for page in page_schemas],
        low_confidence_fields=low_confidence_fields,
    )
    session_record = create_qa_session(
        {
            "split_view": split_view.model_dump(),
            "document": document_schema.model_dump(),
            "pages": [item.model_dump() for item in page_schemas],
            "validation": validation.model_dump(),
        }
    )
    return QAReviewResponse(
        session_id=session_record["session_id"],
        status=session_record["status"],
        split_view=split_view,
        document=document_schema,
        pages=page_schemas,
        validation=validation,
    )


@app.get("/api/v1/qa1/review/{session_id}", response_model=QAReviewResponse)
def qa1_review_get(session_id: str) -> QAReviewResponse:
    record = get_qa_session(session_id)
    if record is None:
        raise HTTPException(status_code=404, detail="QA session not found.")
    return QAReviewResponse(
        session_id=record["session_id"],
        status=record["status"],
        split_view=SplitViewPayload(**record["split_view"]),
        document=KIEResult(**record["document"]),
        pages=[OCRKIEPageResult(**item) for item in record["pages"]],
        validation=ValidationResult(**record["validation"]) if record.get("validation") else None,
    )


@app.post("/api/v1/qa2/decision", response_model=QA2DecisionResponse)
def qa2_decision(request: QA2DecisionRequest) -> QA2DecisionResponse:
    record = get_qa_session(request.session_id)
    if record is None:
        raise HTTPException(status_code=404, detail="QA session not found.")

    if request.action == "approve":
        updated = update_qa_session(
            request.session_id,
            {
                "status": "APPROVED",
                "qa2_reason": request.reason,
                "rollback_stage": None,
            },
        )
        assert updated is not None
        return QA2DecisionResponse(
            session_id=request.session_id,
            status="APPROVED",
            rollback_stage=None,
            message="Document approved in QA2.",
        )

    rollback_stage = request.rollback_stage or "QA1"
    updated = update_qa_session(
        request.session_id,
        {
            "status": "REJECTED",
            "qa2_reason": request.reason,
            "rollback_stage": rollback_stage,
        },
    )
    assert updated is not None
    return QA2DecisionResponse(
        session_id=request.session_id,
        status="REJECTED",
        rollback_stage=rollback_stage,
        message=f"Document rejected in QA2. Rolled back to {rollback_stage}.",
    )


@app.post("/api/v1/feedback", response_model=FeedbackResponse)
def submit_feedback(request: FeedbackRequest) -> FeedbackResponse:
    """
    Submit user QA feedback when the AI extracts fields incorrectly.
    This triggers incremental learning processes in the background.
    """
    saved_count = 0
    for item in request.corrections:
        try:
            save_feedback(
                original_text=item.original_text,
                corrected_text=item.corrected_text,
                field_name=item.field_name,
                document_id=item.document_id
            )
            saved_count += 1
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Feedback save failed: {e}")

    if saved_count > 0:
        try:
            retrain_incremental_from_feedback(min_frequency=2)
        except Exception:
            # Keep feedback API stable even if retraining fails.
            pass

    return FeedbackResponse(status="success", saved_count=saved_count)


@app.post("/api/v1/incremental-learning/retrain", response_model=IncrementalLearningStatusResponse)
def retrain_incremental_learning(
    request: IncrementalLearningRetrainRequest,
) -> IncrementalLearningStatusResponse:
    result = retrain_incremental_from_feedback(min_frequency=request.min_frequency)
    return IncrementalLearningStatusResponse(status="success", **result)


@app.get("/api/v1/incremental-learning/status", response_model=IncrementalLearningStatusResponse)
def incremental_learning_status() -> IncrementalLearningStatusResponse:
    if not DEFAULT_LEXICON_PATH.exists():
        return IncrementalLearningStatusResponse(
            status="success",
            lexicon_path=str(DEFAULT_LEXICON_PATH),
            updated_entries=0,
            feedback_records=0,
        )
    result = get_incremental_status(lexicon_path=DEFAULT_LEXICON_PATH)
    return IncrementalLearningStatusResponse(status="success", **result)


from pydantic import BaseModel
class NLPCorrectRequest(BaseModel):
    text: str

class NLPCorrectResponse(BaseModel):
    original: str
    corrected: str

@app.post("/api/v1/nlp-correct", response_model=NLPCorrectResponse)
def nlp_correct_text(request: NLPCorrectRequest) -> NLPCorrectResponse:
    """
    Correct OCR spelling mistakes using a pre-trained language model (e.g. PhoBERT variants).
    """
    corrected = correct_text_nlp(request.text)
    return NLPCorrectResponse(original=request.text, corrected=corrected)
=======
>>>>>>> fa883a38ced3be0325d8d4a97f8c1c11e446b43c
