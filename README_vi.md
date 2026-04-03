# VN-Digitize-AI

Một công cụ OCR và tiền xử lý tài liệu cấp sản xuất, có tính xác định cao, được thiết kế chuyên biệt để xử lý cả tài liệu scan và ảnh chụp từ thiết bị di động, hỗ trợ tối ưu việc trích xuất văn bản tiếng Việt.

VN-Digitize-AI biến đổi các hình ảnh thô thành file sạch sẽ, được chuẩn hóa và sẵn sàng cho OCR. Nó trích xuất văn bản sử dụng phương pháp kết hợp Hybrid giữa Tesseract và VietOCR, đồng thời cung cấp khả năng tự động tóm tắt tài liệu hoàn toàn cục bộ bằng các LLM thông qua Ollama. Toàn bộ tính năng này được kết nối qua một ứng dụng FastAPI mạnh mẽ.

## Các Tính Năng Chính

- **Tiền Xử Lý Tài Liệu Nâng Cao**:
  - Tự động cắt (auto-crop) và căn chỉnh độ lệch (deskew).
  - Loại bỏ bóng đổ và vùng ố vàng chuyên biệt cho ảnh chụp.
  - Khử nhiễu và nhị phân hóa thích ứng (có thể tùy chỉnh).
  - **Bảo Tồn Dấu Mộc Đỏ**: Chuyên phát hiện và giữ lại các chi tiết mực đỏ (như con dấu chính thức của nhà nước/doanh nghiệp Việt Nam), vốn thường bị mất trong các quá trình nhị phân hóa thông thường.
  - Nhận diện và tự động loại bỏ các trang trắng.
- **OCR Tiếng Việt Độ Chính Xác Cao**:
  - Tận dụng **Tesseract** để phân tích bố cục văn bản, xác định bounding box (khung chữ) cho từng dòng cực kì hiệu quả.
  - Đưa các bounding box đã cắt vào model **VietOCR** (`vgg_transformer`) để thực hiện nhận dạng văn bản tiếng Việt với sai số thấp nhất (SOTA text recognition).
- **Trích Xuất Thông Tin KIE (Key Information Extraction)**:
  - Trích xuất thông tin có cấu trúc (số văn bản, ngày ban hành, cơ quan, loại văn bản, trích yếu) từ các văn bản hành chính/pháp lý tiếng Việt.
  - Sử dụng phương pháp **Hybrid**: ưu tiên nhận diện pattern bằng Regex cho kết quả chính xác cao, kết hợp suy luận dự phòng bằng LLM cho các trường khó.
- **Tóm Tắt Tài Liệu**:
  - Tự động tóm tắt văn bản một cách kín đáo, an toàn ngay trên máy tính của bạn bằng **Ollama** (mặc định cấu hình gọi tới model `qwen2.5:3b-instruct`).
- **Tích Hợp Scanner & Chia Mã Vạch**:
  - Hỗ trợ kết nối và nhận lệnh trực tiếp từ các máy quét vật lý (scanner).
  - Tự động chia tách tài liệu thành những văn bản nhỏ riêng biệt dựa trên mã vạch được nhận diện trên trang.
- **Backend FastAPI**:
  - API REST hiệu năng cao.
  - Cung cấp các endpoint riêng lẻ (tiền xử lý, OCR, tóm tắt) hoặc một luồng xử lý toàn trình (end-to-end pipeline).

## Chạy Thử (Demo)

Bạn có thể chạy thử trực tiếp quy trình toàn trình (Tiền xử lý -> OCR -> Tóm tắt) bằng tệp lệnh `demo.py` đã chuẩn bị sẵn:

```bash
python demo.py
```
*Hãy đảm bảo bạn đã copy file ảnh muốn test và đặt tên `image.png` ở thư mục gốc trước khi chạy, hoặc trỏ đường dẫn biến `input_image_path` tới tệp của bạn trong script. Toàn bộ các kết quả (ảnh đã làm sạch, file OCR `.json` cùng văn bản gốc, và text tóm tắt) sẽ được hệ thống lưu trong thư mục `data/manual_preprocess/`.*

## Cài Đặt

### Yêu Cầu Môi Trường
1. **Python 3.10+** (Khuyên dùng)
2. **Tesseract OCR**: Phải được cài sẵn trên hệ thống của bạn và thiết lập ở biến môi trường PATH (trên Windows, app sẽ tự lấy đường dẫn mặc định `C:/Program Files/Tesseract-OCR/tesseract.exe`).
3. **Ollama**: (Không bắt buộc, chỉ yêu cầu khi chạy tính năng summary). Đảm bảo Ollama đã được khởi chạy trên local với model đã tải sẵn (vd: `ollama run qwen2.5:3b-instruct`).

### Trình Tự Cài Đặt

Cài đặt các gói thư viện Python cần thiết:

```bash
pip install -r requirements.txt
```

*Lưu ý: Trong quá trình chạy API phần quét OCR lần đầu, model `vietocr` sẽ tự động tải các tham số (vgg_transformer weights) mất chút thời gian.*

## Các API Endpoint Chính

Bạn có thể khởi động HTTP Server:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Các Endpoint Cốt Lõi

- **`POST /api/v1/scan-upload`**: Nhận lệnh điều khiển scan từ máy scan kết nối thẳng vào máy tính hoặc upload tệp hình ảnh. File ảnh tự động được chia thành các bó tài liệu (bundle) nếu phần mềm tìm thấy trang chứa mã vạch.
- **`POST /api/v1/preprocess`**: Thực hiện lệnh tiền xử lý các ảnh đã có sẵn ở file system.
- **`POST /api/v1/upload-preprocess`**: Endpoint hỗ trợ gộp, cho phép upload tệp và tiền xử lý tức thì (auto-crop, deskew, nhị phân tài liệu,...).
- **`POST /api/v1/ocr-fulltext`**: Trích xuất toàn bộ lượng chữ từ hình ảnh bằng phương pháp Hybrid kết hợp Tesseract + VietOCR.
- **`POST /api/v1/kie`**: Trích xuất thông tin có cấu trúc (KIE) trực tiếp từ string văn bản OCR.
- **`POST /api/v1/ocr-kie`**: Luồng xử lý toàn trình từ hình ảnh -> OCR -> KIE. Trả về cả kết quả KIE từng trang (kèm theo bounding box) và kết quả gộp cho toàn bộ tài liệu.
- **`POST /api/v1/auto-summary`**: Nhận một string văn bản để gửi tóm tắt qua local model Ollama.
- **`POST /api/v1/ocr-auto-summary`**: Endpoint cực kỳ thuận tiện giúp từ lúc chụp ảnh OCR ra đến lúc tóm tắt gộp luôn trong một lượt request API duy nhất.

Bạn nên xem trực tiếp qua giao diện Swagger/OpenAPI tại địa chỉ `http://localhost:8000/docs` ngay khi server vừa bật xong. Đây là nơi bạn sẽ thấy được chi tiết cấu trúc Request nhằm tùy biến bật/tắt mọi tính năng mạnh mẽ khác (như `preserve_red_stamp` hay `shadow_removal`).

## Kiểm Thử (Testing)

Dự án có đi kèm các quy trình kiểm thử hoàn chỉnh với `pytest`, cho phép bạn thử nghiệm nhanh chóng cả Core Services lẫn các API Endpoints.

```bash
pytest
```
