# Tóm Tắt Công Nghệ & Tech Stack Đã Tích Hợp (VN-Digitize-AI)

Đây là bản tóm tắt chi tiết toàn bộ các Công nghệ (Technologies), Thư viện (Libraries), và Framework (Tech Stack) chuyên sâu đã được ứng dụng để xây dựng lớp Kiến trúc Document Intelligence (Số hoá văn bản) ở phiên bản hiện tại.

---

## 1. Hạ Tầng Xử Lý Cốt Lõi (Core Framework & Language)
- **Python (3.9+)**: Ngôn ngữ lập trình chủ đạo đảm nhận liên kết toàn bộ pipeline.
- **FastAPI**: Web framework tiên tiến nhất của Python, được sử dụng để xây dựng các API endpoints nội bộ nhờ khả năng chạy cực mượt, auto-validation (qua **Pydantic Schema**) và document hóa (Tự động sinh Swagger UI).
- **Uvicorn**: ASGI Server tốc độ cao dùng để host FastAPI application.

## 2. Thị Giác Máy Tính & Bóc Tách Chữ (Computer Vision & OCR)
- **PaddleOCR & PaddlePaddle**: 
  - Khung Deep Learning trụ cột của hệ thống, thay thế toàn bộ cho Tesseract.
  - Sử dụng Multi-language model tối ưu hoá chuyên trách ngôn ngữ thứ cấp Tiếng Việt (`lang=vi`). Chở sức mạnh nhận diện Ký tự (Text Recognition) và phát hiện Góc lật ảnh (`angle_cls`).
- **PP-Structure (Module từ PaddleOCR)**: Chuyên trách Layout Analysis (đọc hiểu Bố cục mặt giấy) và móc hàm bóc tách cấu trúc Table (Bảng Biểu).
- **OpenCV (`opencv-python`) & NumPy**: Trái tim của Engine Tiền xử lý (Pre-processing). Đảm nhận các thuật toán ma trận hình ảnh như: Adaptive Thresholding (Nhị phân hoá), Deskewing (Xoay góc minAreaRect), Khử bóng đổ mờ sương mờ (Illumination normalise)...
- **Pillow / PIL**: Hỗ trợ chuyển đổi Color-space linh hoạt giữa CV2 và các modules khác.

## 3. Trí Tuệ Nhân Tạo & Khai Phá Ngôn Ngữ (AI & NLP)
- **Ollama**: Nền tảng Local LLM chạy hoàn toàn dưới máy cá nhân. Đóng vai trò là Engine Bóc tách linh hoạt (Dynamic KIE) và chẩn đoán nội dung, dùng chung Model `qwen2.5:3b-instruct` cho mọi logic từ Summary -> JSON Keys Extraction.
- **Biểu thức Chính quy (Python `re` / Regex)**: Đảm đương Phase-1 Data Extraction, bóc chuẩn xác các chuỗi logic tĩnh (Mã số công văn Hành chính, Format ngày tháng). Đóng vai trò mỏ neo cho Hệ thống Phân mảnh PDF `document_splitter.py`.

## 4. Xử Lý Kiến Trúc Đầu Ra (Output Engineering / Post-Processing)
- **ReportLab**: Engine lõi chịu trách nhiệm "vẽ" file PDF xuất xưởng. Tại đây nó đảm nhận tính năng Render Text tàng hình (Invisible Text Rendering) đan chồng lên Ảnh, cho ra chuẩn Searchable PDF/A. Kéo giãn trục toạ độ thông minh.
- **BeautifulSoup (`beautifulsoup4`)**: Nằm tại tầng Layout Analysis, thực hiện cào rách cấu trúc HTML mà `PP-Structure` nôn ra để convert tự động thành Mảng JSON Array thuần khiết phục vụ Frontend.
- **Ultralytics (YOLO) & PyTorch**: (Hạ tầng Post-processing Pipeline) Bệ phóng đã tích hợp sẵn cho việc load trọng số Model `.pt` của YOLO nhằm vẽ Bounding Box lên các thực thể lạ như Con Dấu Đỏ/Chữ Ký.

## 5. Kiến Trúc Luồng Bất Đồng Bộ & Data (Async Architecture - Giai đoạn Tiếp Theo)
*(Tech stack đã cài cắm dependencies sẵn sàng nhưng chờ setup server)*
- **Celery**: Lấy nhiệm vụ Heavy-weight (Nhận diện OCR 1000 page) từ FastAPI tống xuống chạy nền ở Background Worker.
- **Redis**: Đóng vai trò là RAM Message Broker ở port `6379`, làm trạm trung chuyển điều phối tin nhắn Job Task Queue cho Celery.
- **SQLAlchemy (ORM) + SQLite**: Làm kho chứa State lưu trữ các Lịch sử tiến độ Task và lưu lại phản hồi sửa chữ sai từ bộ phận Nhập liệu (Human-in-the-Loop AI Feedback).
