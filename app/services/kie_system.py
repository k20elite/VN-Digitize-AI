import json
import logging
import re
from typing import Any, Dict, List

logger = logging.getLogger(__name__)

def _union_bboxes(bboxes: List[List[int]]) -> List[int]:
    """
    Calculate the bounding box union for a list of [x, y, w, h] boxes.
    """
    if not bboxes:
        return [0, 0, 0, 0]
    
    xs = [b[0] for b in bboxes]
    ys = [b[1] for b in bboxes]
    xmaxs = [b[0] + b[2] for b in bboxes]
    ymaxs = [b[1] + b[3] for b in bboxes]

    x_min = min(xs)
    y_min = min(ys)
    x_max = max(xmaxs)
    y_max = max(ymaxs)

    return [x_min, y_min, x_max - x_min, y_max - y_min]

def _clean_text(text: str) -> str:
    """Normalize text for matching by removing excessive whitespace and lowercasing."""
    return re.sub(r'\s+', ' ', str(text)).strip().lower()

def map_value_to_bbox(
    extracted_value: str, 
    ocr_lines: List[Dict[str, Any]]
) -> List[int]:
    """
    Maps an extracted string value back to the original OCR bounding boxes.
    Handles exact matches, substring matches, and multi-line spanning.
    ocr_lines format: [{"text": str, "bbox": [x, y, w, h]}]
    """
    if not extracted_value or not ocr_lines:
        return [0, 0, 0, 0]
        
    val_clean = _clean_text(extracted_value)
    
    # Strategy 1: Exact or substring match within a single line
    for line in ocr_lines:
        line_clean = _clean_text(line.get("text", ""))
        if val_clean in line_clean or line_clean in val_clean:
            return line.get("bbox", [0, 0, 0, 0])
            
    # Strategy 2: Multi-line match (if the extracted value spans across lines)
    # Tokenize the value and find all lines that contain its parts
    val_tokens = val_clean.split()
    matched_bboxes = []
    
    # We assign a line's bbox if it contains a significant chunk of the value
    chunk_size = max(2, len(val_tokens) // 3) 
    
    for line in ocr_lines:
        line_clean = _clean_text(line.get("text", ""))
        # Check if they share enough common words
        common_words = set(val_tokens).intersection(set(line_clean.split()))
        if len(common_words) >= chunk_size:
            matched_bboxes.append(line.get("bbox", [0, 0, 0, 0]))
            
    if matched_bboxes:
        return _union_bboxes(matched_bboxes)
        
    # Strategy 3: Best effort fallback (no match found)
    return [0, 0, 0, 0]

# --- Core KIE Extractor Class ---

class HybridKIEEngine:
    def __init__(self, ollama_url: str = "http://localhost:11434", model: str = "qwen2.5:3b-instruct"):
        self.ollama_url = ollama_url
        self.model = model

    def _extract_regex(self, full_text: str) -> Dict[str, Any]:
        """Stage 1: Regex extraction for standard fields."""
        results = {}
        # Simple regex examples for demonstration
        doc_num_match = re.search(r'[Ss][oố][:\.\s]+(\d+/\d{4}/[\w\-]+|\d+/[\w\-]+)', full_text)
        if doc_num_match:
            results["document_number"] = {"value": doc_num_match.group(1), "confidence": 0.95}
        
        date_match = re.search(r'ng[àa]y\s+(\d{1,2})\s+th[aá]ng\s+(\d{1,2})\s+n[aă]m\s+(\d{4})', full_text, re.I)
        if date_match:
            val = f"ngày {date_match.group(1)} tháng {date_match.group(2)} năm {date_match.group(3)}"
            results["issue_date"] = {"value": val, "confidence": 0.90}
            
        return results

    def _extract_llm(self, full_text: str, templates: List[str]) -> Dict[str, Any]:
        """Stage 2: LLM extraction for context and dynamic templates."""
        # Mock LLM API call for example purposes
        # In production this uses urllib/requests to call self.ollama_url
        mock_llm_response = {
            "document_number": {"value": "73/2024/NĐ-CP", "confidence": 0.8},
            "issue_date": {"value": "ngày 30 tháng 6 năm 2024", "confidence": 0.85},
            "custom_field_1": {"value": "Tòa án TP Hà Nội", "confidence": 0.7} # Mocking dynamic template
        }
        return mock_llm_response

    def extract(self, ocr_output: Dict[str, Any], layout_blocks: List[Dict[str, Any]], templates: List[str] = None) -> Dict[str, Any]:
        """
        Main KIE extraction method.
        Input: 
          - ocr_output: {"full_text": "...", "lines": [{"text": "...", "bbox": [...]}]}
          - layout_blocks: PP-Structure blocks (header, table, etc.) for contextual filtering.
          - templates: List of dynamic field names/descriptions.
        """
        ocr_lines = ocr_output.get("lines", [])
        full_text = "\n".join([line.get("text", "") for line in ocr_lines])
        
        # 1. Hybrid Extraction
        regex_results = self._extract_regex(full_text)
        llm_results = self._extract_llm(full_text, templates=templates or [])
        
        # Merge (prefer Regex if confidence > 0.85, else LLM)
        merged_results = {}
        all_keys = set(regex_results.keys()).union(set(llm_results.keys()))
        for key in all_keys:
            r_val = regex_results.get(key, {})
            l_val = llm_results.get(key, {})
            
            if r_val.get("confidence", 0) > 0.85:
                merged_results[key] = r_val
            else:
                merged_results[key] = l_val if l_val.get("confidence", 0) > r_val.get("confidence", 0) else r_val

        # 2. Map coordinates (BBox) and format response
        final_fields = []
        for name, data in merged_results.items():
            if not data.get("value"):
                continue
                
            val = data["value"]
            bbox = map_value_to_bbox(val, ocr_lines)
            
            final_fields.append({
                "name": name,
                "value": val,
                "bbox": bbox,
                "confidence": data.get("confidence", 0.0)
            })

        return {"fields": final_fields}

# Example matching logic block
if __name__ == "__main__":
    mock_ocr = {
        "lines": [
            {"text": "CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM", "bbox": [100, 20, 400, 20]},
            {"text": "Độc lập - Tự do - Hạnh phúc", "bbox": [120, 50, 300, 20]},
            {"text": "Số: 73/2024/NĐ-CP", "bbox": [50, 100, 200, 20]}, # target bbox
            {"text": "Hà Nội, ngày 30 tháng 6 năm 2024", "bbox": [350, 100, 250, 20]}
        ]
    }
    
    mock_layout = []
    
    engine = HybridKIEEngine()
    result = engine.extract(ocr_output=mock_ocr, layout_blocks=mock_layout, templates=["custom_field_1"])
    
    print(json.dumps(result, ensure_ascii=False, indent=2))
