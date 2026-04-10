# VN-Digitize-AI

Hệ thống số hóa tài liệu tiếng Việt theo pipeline OCR thực chiến:  
**tiền xử lý ảnh → OCR → bóc tách trường dữ liệu (KIE) → kiểm tra hậu xử lý (con dấu/chữ ký, bảng) → sửa lỗi chính tả NLP → QA nhiều bước → xuất PDF searchable.**

VN-Digitize-AI là engine tiền xử lý và OCR deterministic, production-grade, được thiết kế đặc biệt để xử lý cả tài liệu scan và chụp camera, với hỗ trợ tối ưu cho văn bản tiếng Việt.

---

## 1. Tính năng chính

- **Tiền xử lý ảnh tài liệu nâng cao**:
  - Deskew, auto-crop, khử bóng, khử nhiễu, xử lý ố vàng.
  - Bảo tồn dấu đỏ (red stamp preservation) – phát hiện và giữ lại dấu đỏ của cơ quan/đơn vị mà không bị mất trong quá trình nhị phân hóa.
  - Phát hiện và tự động loại trang trắng.

- **OCR tiếng Việt độ chính xác cao**:
  - Sử dụng hybrid **Tesseract** (layout analysis + bounding box) + **VietOCR / deepdoc_vietocr** (`vgg_transformer` model).
  - Trả về `full_text`, `lines` kèm `bbox` và `confidence`.

- **KIE (Key Information Extraction)**:
  - Hybrid: Regex + LLM (qua Ollama) hỗ trợ 5 trường chuẩn và trường tùy biến theo template.

- **Hậu xử lý**:
  - Detect con dấu / chữ ký bằng YOLO.
  - Trích xuất bảng từ kết quả OCR.

- **NLP Correction**:
  - Sửa lỗi chính tả OCR tự động (`/api/v1/nlp-correct`).

- **QA Flow & Feedback**:
  - QA1 / QA2 với feedback loop và incremental learning.

- **Xuất kết quả**:
  - PDF searchable và PDF-A.

- **Tính năng khác**:
  - Hỗ trợ scanner vật lý + tách tài liệu theo barcode.
  - Chạy bất đồng bộ với Celery + Redis.
  - Tóm tắt tài liệu bằng LLM cục bộ qua Ollama.

---

## 2. Kiến trúc pipeline (UI 7 bước)

Luồng khuyến nghị:

1. Scan / Upload  
2. Tiền xử lý  
3. OCR (raw text)  
4. KIE + Bounding box  
   4.1 Detect con dấu / chữ ký (YOLO)  
   4.2 Sửa lỗi chính tả (NLP) → Tóm tắt  
5. QA1  
6. QA2  
7. Export PDF + Archive

---

## 3. Yêu cầu môi trường

- Python 3.10+
- Hệ điều hành: Windows / Linux (đã kiểm thử chủ yếu trên Windows)
- Tesseract OCR đã cài đặt hệ thống
- Ollama (nếu dùng tính năng summary / KIE fallback qua LLM)

### Cài đặt

```bash
pip install -r requirements.txt
