# VN-Digitize-AI

<<<<<<< HEAD
Hệ thống số hóa tài liệu tiếng Việt theo pipeline OCR thực chiến:
tiền xử lý ảnh, OCR, bóc tách trường dữ liệu (KIE), kiểm tra hậu xử lý
(detect con dấu/chữ ký, bảng), sửa lỗi chính tả bằng NLP, QA nhiều bước,
và xuất PDF searchable.

## 1) Tính năng chính

- Tiền xử lý ảnh tài liệu: deskew, auto-crop, khử bóng, khử nhiễu, xử lý ố vàng, loại trang trắng.
- OCR tiếng Việt bằng `deepdoc_vietocr`, trả về `full_text` và `lines` có `bbox` + `confidence`.
- KIE hybrid (Regex + LLM qua Ollama) cho 5 trường chuẩn và trường tùy biến theo template.
- Hậu xử lý: detect `stamp/signature` bằng YOLO, trích bảng từ OCR lines.
- NLP correction cho lỗi chính tả OCR (`/api/v1/nlp-correct`).
- QA flow (QA1/QA2), feedback loop và incremental learning.
- Xuất PDF searchable/PDF-A.
- Hỗ trợ chạy bất đồng bộ với Celery + Redis cho tác vụ nặng.

## 2) Kiến trúc pipeline (UI 7 bước)

Luồng khuyến nghị:

1. Scan/Upload
2. Tiền xử lý
3. OCR (raw text)
4. KIE + Bounding box
4.1 Detect con dấu/chữ ký (YOLO)
4.2 Sửa lỗi chính tả (NLP) -> Summary từ text đã sửa
5. QA1
6. QA2
7. Export PDF + Archive

## 3) Yêu cầu môi trường

- Python 3.10+
- Windows/Linux đều chạy được (đã kiểm thử chủ yếu trên Windows)
- Cài dependency:
=======
A production-grade, deterministic document preprocessing and OCR engine designed specifically to handle both scanned and camera-captured documents, with specialized support for Vietnamese text.

VN-Digitize-AI transforms raw images into clean, normalized, and OCR-ready files, extracts text using a hybrid Tesseract + VietOCR approach, and provides document summarization capabilities using local LLMs via Ollama. It exposes all these features through a robust FastAPI application.

## Key Features

- **Advanced Document Preprocessing**:
  - Automatic cropping and deskewing.
  - Shadow and yellow stain removal for camera-captured images.
  - Denoising and adaptive binarization (configurable).
  - **Red Stamp Preservation**: Specifically detects and preserves red ink elements (like official company/government stamps) which are often lost during normal binarization pipelines.
  - Blank page detection and automatic removal.
- **High-Accuracy Vietnamese OCR**:
  - Utilizes **Tesseract** for robust layout analysis and line bounding box detection.
  - Feeds cropped bounding boxes into **VietOCR** (`vgg_transformer` model) for state-of-the-art Vietnamese text recognition.
- **Document Summarization**:
  - Summarizes extracted OCR text locally, privately, and securely using **Ollama** (defaults to `qwen2.5:3b-instruct`).
- **Scanner & Barcode Integration**:
  - Supports direct integration with physical scanners.
  - Automatically splits document bundles based on detected barcodes.
- **FastAPI Backend**:
  - High-performance REST API.
  - Modular endpoints for preprocessing, OCR, and summarization, or full end-to-end pipelines.

## Quick Start Demo

You can try the full pipeline (Preprocessing -> OCR -> Summary) using the included `demo.py` script:

```bash
python demo.py
```
*Make sure to place an `image.png` in the root directory before running or update the script's `input_image_path`. The outputs (cleaned images, OCR JSONs, and text summaries) will be saved in the `data/manual_preprocess/` directory.*

## Installation

### Prerequisites
1. **Python 3.10+** (Recommended)
2. **Tesseract OCR**: Needs to be installed on your system. It relies on standard system PATH or default Windows installation paths (`C:/Program Files/Tesseract-OCR/tesseract.exe`).
3. **Ollama**: (Optional, required only for auto-summarization). Needs to be installed and running locally with the target model pulled (e.g., `ollama run qwen2.5:3b-instruct`).

### Setup

Install the required Python dependencies:
>>>>>>> fa883a38ced3be0325d8d4a97f8c1c11e446b43c

```bash
pip install -r requirements.txt
```

<<<<<<< HEAD
Ghi chú:
- Nếu dùng summary/KIE fallback qua LLM, cần Ollama local (mặc định gọi `http://127.0.0.1:11434`).
- Một số model OCR/detect có thể tải ở lần chạy đầu, nên request đầu sẽ chậm hơn.

## 4) Chạy nhanh

Khởi động API:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Mở tài liệu API:
- `http://localhost:8000/docs`

Mở UI:
- `http://localhost:8000/`

## 5) Các endpoint quan trọng

- `POST /api/v1/scan-upload`
- `POST /api/v1/preprocess`
- `POST /api/v1/upload-preprocess`
- `POST /api/v1/ocr-fulltext`
- `POST /api/v1/kie`
- `POST /api/v1/ocr-kie`
- `POST /api/v1/extract-fields`
- `POST /api/v1/split-document`
- `POST /api/v1/postprocess-check` (stamp/signature/table)
- `POST /api/v1/nlp-correct`
- `POST /api/v1/auto-summary`
- `POST /api/v1/ocr-auto-summary`
- `POST /api/v1/qa1/review-create`
- `POST /api/v1/qa2/decision`
- `POST /api/v1/export-pdf-searchable`
- `POST /api/v1/archive/store`
- `POST /api/v1/feedback`
- `POST /api/v1/async/ocr-kie`
- `POST /api/v1/async/split-document`
- `GET /api/v1/task/{task_id}`

## 6) Chạy test
=======
*Note: The first time you run the OCR service, `vietocr` will download its `vgg_transformer` weights.*

## Main API Endpoints

Start the API server:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Core Endpoints

- **`POST /api/v1/scan-upload`**: Scan documents from a connected physical scanner or upload image files. Automatically separates documents into bundles if barcodes are found.
- **`POST /api/v1/preprocess`**: Run the configurable preprocessing pipeline on local filesystem images.
- **`POST /api/v1/upload-preprocess`**: Unified endpoint to upload files and immediately run the preprocessing pipeline (auto-crop, deskew, binarize, etc.).
- **`POST /api/v1/ocr-fulltext`**: Extract full text from images using the hybrid Tesseract + VietOCR method.
- **`POST /api/v1/auto-summary`**: Submit pure text to be summarized by the local Ollama model.
- **`POST /api/v1/ocr-auto-summary`**: Convenience endpoint for end-to-end OCR extraction followed by immediate summarization.

Review the Swagger/OpenAPI documentation at `http://localhost:8000/docs` while the server is running to detailed request options, including how to toggle specific preprocessing features (like `preserve_red_stamp` or `shadow_removal`).

## Testing

The repository includes a comprehensive `pytest` suite testing both API endpoints and core services.
>>>>>>> fa883a38ced3be0325d8d4a97f8c1c11e446b43c

```bash
pytest
```
<<<<<<< HEAD

Hoặc chạy nhanh một nhóm test:

```bash
pytest tests/test_api_ocr_summary.py -q
```

## 7) Cấu trúc thư mục chính

- `app/`: API, schema, service, web UI.
- `tests/`: bộ test pytest.
- `deepdoc_vietocr/`: engine OCR.
- `data/`: dữ liệu runtime (raw/preprocessed/qa_sessions/exported/archive/models).
=======
>>>>>>> fa883a38ced3be0325d8d4a97f8c1c11e446b43c
