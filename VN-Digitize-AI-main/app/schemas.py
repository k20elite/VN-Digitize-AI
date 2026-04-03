from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class ScannerSettings(BaseModel):
    dpi: int = Field(default=300, ge=75, le=1200)
    color_mode: Literal["color", "grayscale", "bw"] = "color"


class ScanUploadResponse(BaseModel):
    class BundleInfo(BaseModel):
        bundle_id: str
        barcode: str | None
        pages: list[str]

    source: Literal["scanner", "upload"]
    total_pages: int
    bundles: list[BundleInfo]
    saved_pages: list[str]


class PreprocessOptions(BaseModel):
    deskew: bool = True
    auto_crop: bool = True
    shadow_removal: bool = True
    denoise: bool = True
    remove_yellow_stains: bool = True
    binarize: bool = False
    preserve_red_stamp: bool = True
    remove_blank_pages: bool = True
    blank_ratio_threshold: float = Field(default=0.006, gt=0.0, lt=1.0)


class PreprocessRequest(BaseModel):
    input_paths: list[str] = Field(min_length=1)
    options: PreprocessOptions = PreprocessOptions()


class PreprocessResult(BaseModel):
    input_path: str
    output_path: str | None
    skipped_as_blank: bool


class PreprocessResponse(BaseModel):
    total_inputs: int
    total_outputs: int
    results: list[PreprocessResult]


class UploadPreprocessResponse(BaseModel):
    total_uploaded: int
    total_outputs: int
    saved_pages: list[str]
    results: list[PreprocessResult]


class OCRRequest(BaseModel):
    input_paths: list[str] = Field(min_length=1)
    lang: str = "vie"
    psm: int = Field(default=6, ge=0, le=13)
    oem: int = Field(default=3, ge=0, le=3)


class OCRLine(BaseModel):
    text: str
    bbox: list[int]
    confidence: float


class OCRPageResult(BaseModel):
    input_path: str
    full_text: str
    lines: list[OCRLine]


class OCRResponse(BaseModel):
    total_pages: int
    pages: list[OCRPageResult]


class AutoSummaryRequest(BaseModel):
    text: str = Field(min_length=1)
    model: str = "qwen2.5:3b-instruct"
    ollama_url: str = "http://127.0.0.1:11434"
    max_words: int = Field(default=160, ge=40, le=500)


class AutoSummaryResponse(BaseModel):
    summary: str
    model: str


class OCRAutoSummaryRequest(BaseModel):
    input_paths: list[str] = Field(min_length=1)
    lang: str = "vie"
    psm: int = Field(default=6, ge=0, le=13)
    oem: int = Field(default=3, ge=0, le=3)
    model: str = "qwen2.5:3b-instruct"
    ollama_url: str = "http://127.0.0.1:11434"
    max_words: int = Field(default=160, ge=40, le=500)


class OCRAutoSummaryResponse(BaseModel):
    ocr: OCRResponse
    summary: str
    model: str


# ---------------------------------------------------------------------------
# KIE — Key Information Extraction
# ---------------------------------------------------------------------------


class KIEField(BaseModel):
    """A single extracted field with its value and extraction confidence."""

    value: str | None = None
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)


class CustomFieldDef(BaseModel):
    """
    Định nghĩa một trường KIE tuỳ chỉnh.

    Attributes:
        field_key:      Tên trường trong JSON output (VD: "ten_bi_cao").
        description:    Mô tả cho LLM — trả lời câu hỏi "trường này chứa thông tin gì?".
                        Càng chi tiết thì LLM càng nhận diện chính xác.
        regex_pattern:  (Tuỳ chọn) Regex để trích xuất trước bằng pattern matching.
                        Nếu khai báo và match được thì dùng kết quả regex (độ tin cậy cao hơn LLM).
    """

    field_key: str = Field(
        min_length=1,
        pattern=r'^[a-z][a-z0-9_]*$',
        description="Tên trường (lowercase, underscore). VD: ten_bi_cao",
    )
    description: str = Field(
        min_length=5,
        description="Mô tả ngữ nghĩa để LLM hiểu cần trích xuất gì.",
    )
    regex_pattern: str | None = Field(
        default=None,
        description="(Tuỳ chọn) Regex pattern để bóc tách. Group 1 là giá trị cần lấy.",
    )


class KIETemplate(BaseModel):
    """
    Template cấu hình trích xuất cho một loại đơn vị / loại văn bản.

    Ví dụ:
      template_name: "Tòa án - Bản án sơ thẩm"
      custom_fields:
        - field_key: ten_bi_cao, description: "Họ tên bị cáo"
        - field_key: toi_danh,   description: "Tội danh theo bản án"
    """

    template_name: str = Field(
        default="custom",
        description="Tên mô tả template (hiển thị trong log / output).",
    )
    custom_fields: list[CustomFieldDef] = Field(
        default_factory=list,
        description="Danh sách các trường tuỳ chỉnh cần trích xuất thêm.",
    )


class KIEResult(BaseModel):
    """All five core KIE fields + tuỳ chọn custom_fields for one document (or page)."""

    so_van_ban: KIEField
    ngay_ban_hanh: KIEField
    co_quan_ban_hanh: KIEField
    loai_van_ban: KIEField
    trich_yeu: KIEField
    custom_fields: dict[str, KIEField] = Field(
        default_factory=dict,
        description="Các trường tuỳ chỉnh bóc theo template (key = field_key).",
    )
    model_used: str | None = None  # LLM model that contributed, if any


class KIERequest(BaseModel):
    """Request body for POST /api/v1/kie."""

    text: str = Field(min_length=1)
    model: str = "qwen2.5:3b-instruct"
    ollama_url: str = "http://127.0.0.1:11434"
    use_llm: bool = True
    template: KIETemplate | None = Field(
        default=None,
        description="(Tuỳ chọn) Template cấu hình thêm các trường đặc thù theo đơn vị.",
    )


class KIEResponse(BaseModel):
    """Response for POST /api/v1/kie."""

    result: KIEResult


class OCRKIEPageResult(BaseModel):
    """Per-page result in POST /api/v1/ocr-kie response."""

    input_path: str
    full_text: str
    lines: list[OCRLine]
    kie: KIEResult


class OCRKIERequest(BaseModel):
    """Request body for POST /api/v1/ocr-kie."""

    input_paths: list[str] = Field(min_length=1)
    lang: str = "vie"
    psm: int = Field(default=6, ge=0, le=13)
    oem: int = Field(default=3, ge=0, le=3)
    model: str = "qwen2.5:3b-instruct"
    ollama_url: str = "http://127.0.0.1:11434"
    use_llm: bool = True
    template: KIETemplate | None = Field(
        default=None,
        description="(Tuỳ chọn) Template cấu hình thêm các trường đặc thù theo đơn vị.",
    )


class OCRKIEResponse(BaseModel):
    """
    Response for POST /api/v1/ocr-kie.

    - ``pages``    : per-page results retaining full OCR lines for UI/QA/debug.
    - ``document`` : document-level KIE merged from all pages (business use).
    """

    pages: list[OCRKIEPageResult]
    document: KIEResult
