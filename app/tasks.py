from app.celery_app import celery_app
from app.services.kie_extractor import extract_kie_from_pages, extract_kie
from app.services.ocr import run_ocr_fulltext
from app.services.document_splitter import split_document_by_content
from app.services.preprocessing import run_preprocess_pipeline
from app.services.validation import validate_document_logic
from app.services.kie_field_bbox import map_kie_fields_to_bboxes
from app.services.handwriting import refine_ocr_for_handwriting
import logging

logger = logging.getLogger(__name__)

@celery_app.task(bind=True, name="app.tasks.process_ocr_kie")
def process_ocr_kie(self, request_data: dict) -> dict:
    """
    Task for running OCR and KIE asynchronously.
    request_data should be a dict equivalent to OCRKIERequest.
    """
    try:
        self.update_state(state='PROGRESS', meta={'message': 'Running OCR...'})
        ocr_result = run_ocr_fulltext(
            input_paths=request_data["input_paths"],
            lang=request_data.get("lang", "vie"),
            psm=request_data.get("psm", 3),
            oem=request_data.get("oem", 3),
        )
        if request_data.get("handwriting_support", False):
            ocr_result = {
                **ocr_result,
                "pages": refine_ocr_for_handwriting(ocr_result["pages"]).get("pages", ocr_result["pages"]),
            }

        self.update_state(state='PROGRESS', meta={'message': 'Running KIE extraction...'})
        kie_result = extract_kie_from_pages(
            ocr_pages=ocr_result["pages"],
            model=request_data.get("model", "qwen2.5:3b-instruct"),
            ollama_url=request_data.get("ollama_url", "http://localhost:11434"),
            use_llm=request_data.get("use_llm", True),
            template=request_data.get("template"),
        )
        
        # Build schemas dicts
        pages = []
        for ocr_page, kie_page in zip(ocr_result["pages"], kie_result["pages"]):
            field_bboxes = map_kie_fields_to_bboxes(kie_page["kie"], ocr_page["lines"])
            enriched_kie = dict(kie_page["kie"])
            enriched_kie["field_bboxes"] = field_bboxes
            pages.append({
                "input_path": ocr_page["input_path"],
                "full_text": ocr_page["full_text"],
                "lines": ocr_page["lines"],
                "kie": enriched_kie
            })

        document_kie = dict(kie_result["document"])
        if pages:
            doc_bboxes: dict[str, list[int] | None] = {}
            for field_name in ["so_van_ban", "ngay_ban_hanh", "co_quan_ban_hanh", "loai_van_ban", "trich_yeu"]:
                best_conf = -1.0
                best_bbox = None
                for page in pages:
                    field = page["kie"].get(field_name, {})
                    conf = float(field.get("confidence", 0.0))
                    bbox = page["kie"].get("field_bboxes", {}).get(field_name)
                    if bbox is not None and conf > best_conf:
                        best_conf = conf
                        best_bbox = bbox
                doc_bboxes[field_name] = best_bbox
            for key in document_kie.get("custom_fields", {}).keys():
                best_conf = -1.0
                best_bbox = None
                for page in pages:
                    field = page["kie"].get("custom_fields", {}).get(key, {})
                    conf = float(field.get("confidence", 0.0))
                    bbox = page["kie"].get("field_bboxes", {}).get(key)
                    if bbox is not None and conf > best_conf:
                        best_conf = conf
                        best_bbox = bbox
                doc_bboxes[key] = best_bbox
            document_kie["field_bboxes"] = doc_bboxes

        return {
            "status": "success",
            "pages": pages,
            "document": document_kie
        }
    except Exception as e:
        logger.exception("Task process_ocr_kie failed")
        return {"status": "error", "message": str(e)}

@celery_app.task(bind=True, name="app.tasks.process_split_document")
def process_split_document(self, request_data: dict) -> dict:
    try:
        self.update_state(state='PROGRESS', meta={'message': 'Running OCR...'})
        ocr_result = run_ocr_fulltext(
            input_paths=request_data["input_paths"],
            lang=request_data.get("lang", "vie"),
            psm=request_data.get("psm", 3),
            oem=request_data.get("oem", 3),
        )
        if request_data.get("handwriting_support", False):
            ocr_result = {
                **ocr_result,
                "pages": refine_ocr_for_handwriting(ocr_result["pages"]).get("pages", ocr_result["pages"]),
            }
        self.update_state(state='PROGRESS', meta={'message': 'Running Document Splitting...'})
        split_result = split_document_by_content(
            ocr_pages=ocr_result["pages"],
            model=request_data.get("model", "qwen2.5:3b-instruct"),
            ollama_url=request_data.get("ollama_url", "http://localhost:11434"),
            use_llm=request_data.get("use_llm", True),
            template=request_data.get("template"),
        )
        return {"status": "success", "result": split_result}
    except Exception as e:
        logger.exception("Task process_split_document failed")
        return {"status": "error", "message": str(e)}
