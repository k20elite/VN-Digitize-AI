import logging
from typing import Any

from bs4 import BeautifulSoup

try:
    from paddleocr import PPStructure
except ImportError:
    pass  # Allow graceful degradation or mocking if paddleocr is not installed yet

logger = logging.getLogger(__name__)

# Singleton instance to avoid reloading models into memory
_PP_STRUCTURE_ENGINE = None

def get_pp_structure_engine(lang: str = "vi") -> "PPStructure":
    """
    Initialize and return the PPStructure singleton instance for Layout Analysis and Table Extraction.
    Optimized for batch processing.
    """
    global _PP_STRUCTURE_ENGINE
    if _PP_STRUCTURE_ENGINE is None:
        logger.info(f"Initializing PPStructure engine for lang='{lang}'...")
        _PP_STRUCTURE_ENGINE = PPStructure(lang=lang, show_log=False)
    return _PP_STRUCTURE_ENGINE

def _parse_html_table(html_content: str) -> dict[str, list[list[str]]]:
    """
    Parses an HTML table string returned by PPStructure into a structured JSON dict.
    Returns: {"rows": [["col1", "col2"], ...]}
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    rows: list[list[str]] = []
    
    for tr in soup.find_all('tr'):
        row_data: list[str] = []
        for cell in tr.find_all(['td', 'th']):
            # Clean up the text inside cells, handling possible nested tags
            cell_text = cell.get_text(separator=" ", strip=True)
            row_data.append(cell_text)
        if row_data:
            rows.append(row_data)
            
    return {"rows": rows}

def _merge_text_results(res: list[dict[str, Any]] | str) -> str:
    """
    Merge the raw OCR results from a text-based layout block into a single string.
    Depending on the PaddleOCR version, `res` could be a list of dicts/tuples or a string.
    """
    if not res:
        return ""
    
    if isinstance(res, str):
        return res
        
    merged_parts = []
    for item in res:
        if isinstance(item, dict) and "text" in item:
            merged_parts.append(item["text"])
        elif isinstance(item, tuple) or isinstance(item, list):
            # Format: (poly_box, (text, confidence)) or similar
            if len(item) > 1 and isinstance(item[1], (tuple, list)) and len(item[1]) > 0:
                merged_parts.append(str(item[1][0]))
                
    return "\n".join(merged_parts).strip()

def analyze_document_layout(
    image_path: str, lang: str = "vi"
) -> dict[str, Any]:
    """
    Perform Layout Analysis and Table Extraction on a given image.
    Maintains spatial consistency (bounding boxes) and preserves reading order.
    
    Returns structured JSON:
    {
       "blocks": [
          {
             "type": "header | paragraph | table | ...",
             "bbox": [x, y, w, h],
             "content": "..." | {"rows": [...]}
          }
       ]
    }
    """
    engine = get_pp_structure_engine(lang=lang)
    
    try:
        # returns a list of dictionaries mapping to detected document blocks
        results = engine(image_path)
    except Exception as e:
        logger.error(f"Failed to process layout for {image_path}: {e}")
        raise RuntimeError(f"Layout analysis failed for {image_path}") from e

    blocks = []
    
    for item in results:
        block_type = item.get("type", "paragraph") # title, figure, table, text, header, footer...
        raw_bbox = item.get("bbox", [0, 0, 0, 0])  # [x1, y1, x2, y2]
        res = item.get("res", [])
        
        # Normalize bbox to [x, y, w, h]
        x1, y1, x2, y2 = raw_bbox
        x, y, w, h = int(x1), int(y1), int(x2 - x1), int(y2 - y1)
        normalized_bbox = [x, y, w, h]
        
        # Handle Output Parsing based on Block Type
        if block_type == "table":
            # Extract HTML from `res`
            if isinstance(res, dict) and "html" in res:
                content = _parse_html_table(res["html"])
            else:
                content = {"rows": []}
        else:
            # For non-table blocks (header, text, title, figure, etc.)
            content = _merge_text_results(res)
            
        blocks.append({
            "type": block_type,
            "bbox": normalized_bbox,
            "content": content
        })
        
    return {
        "blocks": blocks
    }

# Example mock execution output (For demonstrating expected JSON schema)
if __name__ == "__main__":
    example_output = {
        "blocks": [
            {
                "type": "header",
                "bbox": [50, 20, 600, 40],
                "content": "CỘNG HOÀ XÃ HỘI CHỦ NGHĨA VIỆT NAM"
            },
            {
                "type": "table",
                "bbox": [50, 100, 600, 200],
                "content": {
                    "rows": [
                        ["STT", "Họ và Tên", "Chức vụ"],
                        ["1", "Nguyễn Văn A", "Giám đốc"]
                    ]
                }
            }
        ]
    }
    print(example_output)
