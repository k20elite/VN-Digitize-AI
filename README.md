# VN-Digitize-AI (Document Intelligence Pipeline)

A production-grade Document Intelligence and Pre-processing software stack, utilizing state-of-the-art Artificial Intelligence to extract complex Vietnamese administrative and legal documents and produce a finalized archival format.

## 🚀 Breakthrough Features

The project has recently undergone a major architectural overhaul, transitioning from a simple PDF parser into a full-scale Document Intelligence System:

- **SOTA PaddleOCR Core**: 
  - The entire pipeline has been routed to PaddleOCR for processing Vietnamese texts (`lang='vi'`). Engineered on a highly optimized RAM Singleton architecture for seamless Batch Processing. Angle classification (`use_angle_cls=True`) eliminates rotation edge-cases.
- **PP-Structure & Table Extraction**: 
  - Precisely reads the entire page layout. Automatically transforms Table entities natively into 2D JSON arrays (`{"rows": [[], []...]}`).
- **Hybrid Key Information Extraction (KIE) with Spatial Mapping**:
  - Dynamically extracts content via Hybrid Regex + LLM (Ollama). Even better, all extracted text values are "Reverse-Hashed" and anchored back to their exact original red Bounding Boxes (`[x,y,w,h]`), acting as a perfect guide for Frontend highlights.
- **Auto-Splitting & Smart TOC Generation**:
  - A smart Regex engine parses Vietnamese document conventions ("Cộng hoà Xã hội...") to deduce where one "Decision" ends and a completely distinct "Lawsuit Application" begins within identical thousand-page PDF scans.
  - Automatically generates hierarchical nested JSON Trees mapping Chapters to Articles.
- **Searchable PDF/A Export Generator**:
  - Going beyond JSON, the system dynamically utilizes ReportLab to render transparent text-layers directly superimposed onto the original scanned imagery (adjusted dynamically for baseline stretching). The export allows users to natively drag-to-highlight/copy text on legacy paper scans.
- **Post-Processing Validation**:
  - Logic Validation: Checks date constraints (e.g. intercepts hallucinated "Year 2099" dates) and validates Document Numbers.
  - NLP Correction: Applies rule-based hotfixes to immediately counter traditional Vietnamese OCR spelling faults.
  - Architecture ready for YOLO Model injections to target hand-drawn signatures and red corporate stamps.

---

## 🛠️ Installation Sequence

### 1. Environmental Requirements
- **Python 3.9+** (Recommended).
- **Ollama**: Ensure you have pulled a Local LLM Model if you wish to run the LLM-based KIE Summary features (e.g.: `ollama pull qwen2.5:3b-instruct`).

### 2. Dependency Setup
We recommend using a virtual environment (venv, conda) to install the core dependencies:

```bash
pip install -r requirements.txt
```

*(Notable dependencies include: fastapi, paddleocr, paddlepaddle, beautifulsoup4, reportlab, and torch. Installing the paddle/ultralytics packages may take some time).*

---

## 🔗 Core API Endpoints (FastAPI)

Deploy the Server out-of-the-box via `uvicorn`:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Access the **Swagger Docs: `http://localhost:8000/docs`** to Test the entire Pipeline Suite:

1. **`POST /api/v1/preprocess`**: Core image manipulation — Deskews, shadow removal, flattening, and adaptive Binarization with Red Stamp Preservation layers.
2. **`POST /api/v1/ocr-fulltext`**: Bounding Box extraction (`[x,y,w,h]`) + Character Recognition via PaddleOCR.
3. **`POST /api/v1/kie`**: Hybrid (Regex + LLM) KIE supporting dynamic templates, now featuring Spatial Bbox Reverse-Mapping.
4. **`POST /api/v1/split`**: *(Internal API Config)* Splits massive incoming PDF batches into intelligently classified units & delivers TOC.
5. **`POST /api/v1/export-pdf`**: *(Internal API Config)* Receives Image + OCR lines to yield a perfect PDF/A 2-layer searchable object.

---

## 🧭 Roadmap (Next Steps)
- Segregate the Fast API engine into a dedicated Background Job queue using `Celery` + `Redis` to withstand massive 1000-page document batch loads without falling victim to HTTP Timeouts.
- Deploy a **Feedback API** pointed at a localized SQLite Database to gather structured Ground-Truth Data adjustments directly from end UI users, establishing a powerful Human-in-the-Loop Incremental Learning architecture.
