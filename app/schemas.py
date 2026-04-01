from __future__ import annotations

from typing import Literal

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
