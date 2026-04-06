# Báo Cáo Cập Nhật Các Tính Năng (Hôm Nay)

Tài liệu này đánh dấu quá trình nâng cấp vòng lặp (iteration) theo định hướng Gap Analysis, nhằm đưa VN-Digitize-AI từ một pipeline cơ bản trở thành Hệ thống Số hóa Văn bản (Document Intelligence) Sản xuất chất lượng cao.

## Lịch Sử Cập Nhật Chính

### 1. Thay đổi Core OCR Engine (PaddleOCR)
- **Vấn đề cũ:** Máy quét sử dụng Tesseract để lấy layout bounding boxes sau đó vứt qua VietOCR. Tesseract hay gặp lỗi đoán sai từ tiếng Việt nếu nhiễu. VietOCR mất rất nhiều tài nguyên để load riêng lẻ.
- **Tính năng cập nhật:** 
  - Vứt bỏ Tesseract. Chuyển hoàn toàn sang **PaddleOCR** cho cả layout và text recognition tiếng Việt (`lang='vi'`).
  - Hỗ trợ tốt xử lý mảng (Batch-processing) qua Singleton Predictor Instance.
  - Tích hợp chuẩn hoá toạ độ `[x1, y1, x2, y2]` sang Box Frontend `[x, y, w, h]`.

### 2. Tích hợp Bóc tách Layout & Bảng biểu (PP-Structure)
- **Tính năng cập nhật:**
  - Nhúng **PP-Structure** để quét bố cục tổng thể tài liệu.
  - Tự động phát hiện loại Content (Header, Paragraph, Table). 
  - Module Parser chuyên dụng sử dụng `BeautifulSoup` để móc Data bảng HTML từ PPStructure sang kiểu cấu trúc File JSON 2 chiều: `{"rows": [ ["col1", "col2"] ]}`.

### 3. Nâng cấp Engine KIE (Spatial Mapping)
- **Tính năng cập nhật:** Bổ sung toạ độ trực diện cho thuật toán bóc tách giá trị KIE.
  - Sau khi LLM (Ollama) hoặc Regex bắt được Value `(e.g: 73/2024/NĐ-CP)`, thuật toán tự động Reverse Mapping bằng String Hashing/Fuzzy để truy hồi và gán nó vào đúng `bbox [x,y,w,h]` của OCR ban đầu.
  - Tận dụng `Union Bboxes` để gom các bbox lại với nhau nếu Value sinh ra vô tình cắt ngang 2 hoặc nhiều dòng OCR gốc.

### 4. Splitting & Smart TOC (Tách PDF Tự động)
- **Tính năng cập nhật:** Xây dựng Engine độc lập `document_splitter.py`.
  - Không còn cắt bằng mã vạch thô sơ, nay hệ thống dùng Text-based Heuristics kết hợp Regex tiếng Việt để truy tìm Quốc hiệu (Cộng Hoà Xã Hội VN...) nhằm xác định đỉnh mốc cắt Trang tài liệu mới.
  - Đọc và Classification được văn bản Hành Chính (Quyết Định / Đơn Khởi Kiện...).
  - Xây dựng sơ đồ cây Mục lục thông minh (JSON Tree format) móc nối cụ thể theo từng "Chương", "Điều".

### 5. Kiểm thử Giao diện Post-processing AI 
- **Tính năng cập nhật:** Bổ sung Lớp lọc chót trước khi Output.
  - **Logic Validation:** Ngăn AI tự sáng tác mốc ngày ban hành "đến từ tương lai". Check lỗi định dạng số văn bản.
  - **NLP Spells:** Regex tự động fix lỗi chính tả tiếng việt.
  - Lót Base sườn (Architecture) chờ đẩy Model YOLOv8 vào để lấy toạ độ đóng Dấu Đỏ/Chữ ký.

### 6. Khởi tạo Pipeline PDF/A (Searchable Layer)
- **Tính năng cập nhật:** Sinh tệp kết quả (Export PDF).
  - Sử dụng ReportLab, tự động tính tỷ lệ Render (Stretch Width) và ghép các Text tàng hình vào đúng mốc toạ độ (flipped plane y-coord) nhằm cho ra 1 Bức ảnh scan được nhưng User có thể Copy / Highlight từng hàng chữ nhờ lớp Mask ẩn sâu bên trong.

Nền tảng hôm nay đã dọn đường cho việc nâng cấp Worker Asynchronous (Celery/Redis) vào tương lai tới.
