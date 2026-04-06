# VN-Digitize-AI (Document Intelligence Pipeline)

Một cấu trúc phần mềm Xử lý Văn bản Hậu kiểm cấp Sản xuất (Production-grade Document Intelligence), sử dụng nền tảng Trí tuệ Nhân tạo hiện đại nhất để bóc tách tài liệu Hành chính - Pháp lý Việt Nam phức tạp và tạo ra định dạng lưu trữ cuối cùng hoàn chỉnh.

## 🚀 Các Tính Năng Đột Phá

Dự án vừa trải qua đại tu lớn về hệ thống Core AI, đánh dấu sự chuyển mình từ một bộ lọc PDF đơn giản trở thành Hệ thống Số hóa Thông minh toàn cục:

- **Hạt nhân PaddleOCR SOTA**: 
  - Toàn bộ pipeline đã được định tuyến sang PaddleOCR để xử lý tiếng Việt (`lang='vi'`) trên kiến trúc RAM Singleton tối ưu nhất cho hàng chờ (Batch Processing). Không còn lỗi góc cạnh do có góc phân tích `use_angle_cls=True`.
- **PP-Structure & Table Extraction (Cấu trúc Bảng Biểu)**: 
  - Đọc chính xác toàn bộ Layout trang giấy. Tự động chuyển đổi các thẻ Bảng biểu (Tables) sang JSON gốc mảng 2 chiều (`{"rows": [[], []...]}`).
- **Key Information Extraction (KIE) Lai ghép có Mapping Không gian**:
  - Tách nội dung động bằng Regex + LLM (Ollama). Tuyệt vời hơn, toàn bộ kết quả bóc tách được thuật toán truy vết ngược (Reverse Hash) ghim chặt vào tọa độ đỏ (Bbox `[x,y,w,h]`) nguyên bản trên ảnh, làm kim chỉ nam hoàn hảo cho Frontend.
- **Tự động Cắt (Auto-Splitting) & Tạo Mục Lục (Smart TOC)**:
  - Máy mài regex thông minh đọc được quy ước mộc dấu/thể thức văn bản "Cộng hoà Xã hội..." để biết đâu là lúc kết thúc 1 Quyết định và bắt đầu 1 Đơn Khởi Kiện trong tệp Scan gộp hàng nghìn trang.
  - Generates ra chuẩn JSON cây phân cấp từ cấp độ *Chương* tới *Điều*.
- **Sinh file Đích Searchable PDF/A**:
  - Không chỉ dừng ở JSON, hệ thống sử dụng ReportLab render vô hình cực chuẩn xác từng chữ OCR ngay trên nền bức ảnh gốc (có bù co giãn baseline) cho phép copy-paste cực nét trên File xuất để sẵn sàng nhét vào Archive Storage của Doanh nghiệp.
- **Post-Processing Vệ sinh dữ liệu**:
  - Logic Validation: Kiểm tra format Số Ký hiệu, Ngày tháng (chặn ngày đến từ năm 2099).
  - NLP Correction: Nhận thẳng các rules để dập ngay lỗi OCR Tiếng Việt truyền thống (VD: "vưỡn đì" -> "vấn đề").
  - Chờ kết nối cổng Load Model YOLO cho việc dò tìm Chữ Ký Tay / Dấu Mộc Đỏ.

---

## 🛠️ Trình Tự Cài Đặt

### 1. Yêu cầu Môi trường
- **Python 3.9+** (Khuyên dùng).
- **Ollama**: Đảm bảo đã pull sẵn một mô hình Local LLM nếu bạn muốn chạy KIE LLM-based Summary (vd: `ollama pull qwen2.5:3b-instruct`).

### 2. Thiết lập Môi trường Pytorch & Thư viện
Bạn nên dùng một môi trường ảo (venv, conda) và cài đặt các phụ thuộc cốt lõi:

```bash
pip install -r requirements.txt
```

*(Các dependencies nổi cộm gồm: fastapi, paddleocr, paddlepaddle, beautifulsoup4, reportlab và torch. Quá trình tải paddle paddle/ultralytics có thể lâu nếu bạn dùng bản pip thuần GPU)*.

---

## 🔗 Các API Endpoint Chính (FastAPI)

Bạn có triển khai Server thông qua `uvicorn`:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Truy cập **Swagger Docs: `http://localhost:8000/docs`** để Test toàn bộ các cổng Pipeline sau:

1. **`POST /api/v1/preprocess`**: Module xử lý gốc — Căn hướng, xử lý bóng tối, làm phẳng, và Binarize mài mực nhưng chống lem đối với Dấu Đỏ.
2. **`POST /api/v1/ocr-fulltext`**: Trích xuất Bounding Boxes (`[x,y,w,h]`) + Nhận dạng chữ (PaddleOCR).
3. **`POST /api/v1/kie`**: Bóc tách KIE lai (Regex + LLM) hỗ trợ Template Động, kết nối Tọa độ Đảo ngược (Spatial Bbox Reverse-Mapping).
4. **`POST /api/v1/split`**: *(Tích hợp Nội suy)* Nhận đầu vào batch OCR để chẻ dọc bộ tài liệu khổng lồ thành array của các Folder File nhỏ hơn + xuất JSON mục lục.
5. **`POST /api/v1/export-pdf`**: *(Tích hợp Searchable PDF)* Đẩy Ảnh + OCR Lines vào để lấy về Object File PDF/A 2 layer chuẩn mực.

---

## 🧭 Lộ trình phát triển tiếp theo (Next Steps)
- Tách luồng Fast API ra luồng Background Job hàng đợi sử dụng `Celery` + `Redis` nhằm gánh chịu các bản án / tài liệu nặng 1000 page siêu khổng lồ mà không bị HTTP Timeout.
- Triển khai **Feedback API** trỏ vào SQLite Database nhằm chuẩn bị sẵn data huấn luyện ngược (Incremental Learning/Human in the Loop) sau khi end user điều chỉnh ở lưới UI Frontend.
