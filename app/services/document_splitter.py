import json
import logging
import re
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# --- Patterns for Boundary Detection ---
# Vietnamese administrative docs almost always start a new document with this motto:
_MOTTO_PATTERN_1 = re.compile(r'c[oọộ]ng\s+h[oòòa]\s+x[aãâ]\s+h[oọộ]i\s+ch[uủư]\s+ngh[iĩỉ]a\s+vi[eệê]t\s+nam', re.I)

# Lawsuit specific or Court docs might also just start with Court names
_COURT_PATTERN = re.compile(r't[oòòa]\s+[aá]n\s+nh[aâ]n\s+d[aâ]n', re.I)

# --- Patterns for Document Classification ---
_TYPES = [
    ("decision", re.compile(r'\bquy[eế]t\s+[dđ][iị]nh\b', re.I)),
    ("report", re.compile(r'\bb[aá]o\s+c[aá]o\b', re.I)),
    ("lawsuit", re.compile(r'\b(đ[oơ]n\s+kh[oở]i\s+ki[eệ]n|b[aả]n\s+[aá]n|kh[aá]ng\s+c[aá]o)\b', re.I)),
]

# --- Patterns for TOC (Hierarchy) ---
# Chương I, Chương II...
_CHAPTER_PATTERN = re.compile(r'^(ch[uư][oơ]ng\s+[ivxlcwm]+)[\.\:\s]*(.*)', re.I)
# Điều 1, Điều 2...
_ARTICLE_PATTERN = re.compile(r'^(đi[eề]u\s+\d+)[\.\:\s]*(.*)', re.I)


def _detect_boundary(page_text: str) -> bool:
    """
    Check if a page is the start of a NEW document.
    We look at the first 15 lines of the OCR text.
    """
    lines = page_text.splitlines()[:15]
    header_text = " ".join(lines)
    
    if _MOTTO_PATTERN_1.search(header_text):
        return True
    
    # Sometimes courts use specific layouts
    if _COURT_PATTERN.search(header_text[:100]):
        # Verify it has some "Số:..." or "Bản án số:..." to confirm it's a first page
        if re.search(r's[oố]\s*:', header_text, re.I):
            return True
            
    return False


def _classify_type(page_text: str) -> str:
    """
    Identify document type from the first few lines.
    """
    lines = page_text.splitlines()[:20]
    header_text = "\n".join(lines)
    
    # Priority matching
    for doc_type_id, pattern in _TYPES:
        if pattern.search(header_text):
            return doc_type_id
            
    return "other"


def _extract_title(page_text: str, doc_type: str) -> str:
    """
    Extremely simple heuristic to grab the document title.
    Usually the line immediately after the document type keyword.
    """
    lines = [ln.strip() for ln in page_text.splitlines() if ln.strip()]
    for i, line in enumerate(lines[:20]):
        # If we see a fully uppercase line that looks like a title
        if doc_type != "other" and doc_type_id_to_vn(doc_type).upper() in line.upper():
            title_parts = [line]
            # Try to grab the abstract (trích yếu) underneath
            if i + 1 < len(lines):
                next_line = lines[i+1]
                if len(next_line) > 10 and not re.match(r'(căn cứ|theo)', next_line, re.I):
                    title_parts.append(next_line)
            return " - ".join(title_parts)
            
    # Fallback: grab first meaningful line 
    for line in lines:
        if len(line) > 15 and not _MOTTO_PATTERN_1.search(line):
            return line
            
    return "Untitled Document"


def doc_type_id_to_vn(type_id: str) -> str:
    mapper = {"decision": "Quyết định", "report": "Báo cáo", "lawsuit": "Đơn/Bản án"}
    return mapper.get(type_id, "Văn bản")


def _build_toc_for_document(pages_texts: List[str], start_page_idx: int) -> List[Dict[str, Any]]:
    """
    Build a nested TOC tree JSON by looking for Chapters and Articles 
    within the document's assigned pages.
    """
    toc_tree = []
    current_chapter = None
    
    for relative_page_idx, page_text in enumerate(pages_texts):
        actual_page_num = start_page_idx + relative_page_idx
        lines = page_text.splitlines()
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Check Chapter
            ch_match = _CHAPTER_PATTERN.match(line)
            if ch_match:
                chapter_title = ch_match.group(1).upper() + (": " + ch_match.group(2) if ch_match.group(2) else "")
                current_chapter = {
                    "title": chapter_title,
                    "page": actual_page_num,
                    "children": []
                }
                toc_tree.append(current_chapter)
                continue
                
            # Check Article
            art_match = _ARTICLE_PATTERN.match(line)
            if art_match:
                article_title = art_match.group(1).capitalize() + (": " + art_match.group(2) if art_match.group(2) else "")
                article_node = {
                    "title": article_title,
                    "page": actual_page_num,
                    "children": []
                }
                if current_chapter is not None:
                    current_chapter["children"].append(article_node)
                else:
                    # Article without a Chapter
                    toc_tree.append(article_node)
                    
    return toc_tree


def split_and_classify_pdf(pages_ocr: List[str]) -> Dict[str, Any]:
    """
    Splits a multi-document PDF into logical document units based on content.
    Returns classified types, boundaries, and a hierarchical TOC.
    pages_ocr: List of text content for each page sequentially.
    """
    if not pages_ocr:
        return {"documents": []}
        
    documents = []
    current_doc: Optional[Dict[str, Any]] = None
    current_doc_text_buffer = []
    
    for i, page_text in enumerate(pages_ocr):
        page_num = i + 1 # 1-indexed
        
        is_boundary = _detect_boundary(page_text)
        
        if is_boundary or current_doc is None:
            # We hit a new document! Seal the previous one.
            if current_doc is not None:
                current_doc["end_page"] = page_num - 1
                # Build TOC for the sealed document
                current_doc["children"] = _build_toc_for_document(
                    current_doc_text_buffer, 
                    current_doc["start_page"]
                )
                documents.append(current_doc)
                
            # Start fresh document
            doc_type = _classify_type(page_text)
            doc_title = _extract_title(page_text, doc_type)
            
            current_doc = {
                "type": doc_type,
                "start_page": page_num,
                "end_page": -1, # To be determined
                "title": doc_title,
                "children": []
            }
            current_doc_text_buffer = [page_text]
        else:
            # Continues existing document
            current_doc_text_buffer.append(page_text)
            
    # Tail cleanup for the final document
    if current_doc is not None:
        current_doc["end_page"] = len(pages_ocr)
        current_doc["children"] = _build_toc_for_document(
            current_doc_text_buffer, 
            current_doc["start_page"]
        )
        documents.append(current_doc)
        
    return {"documents": documents}


if __name__ == "__main__":
    # Example Mock Array representing a batch of 4 pages from noisy OCR
    mock_pdf_ocr = [
        # Page 1: Decision start
        "CỘNG HOÀ XÃ HỘI CHỦ NGHĨA VIỆT NAM\nĐộc lập - Tự do - Hạnh phúc\nQUYẾT ĐỊNH\nVề việc bổ nhiệm cán bộ\nĐiều 1. Bổ nhiệm ông Nguyễn Văn A...",
        # Page 2: Decision continues
        "Điều 2. Các đơn vị có liên quan chịu trách nhiệm thi hành quyết định này.",
        # Page 3: Lawsuit application starts
        "Cộng hòa xã hội chủ nghĩa việt nam\nĐỘC LẬP TỰ DO\nĐƠN KHỞI KIỆN\nKính gửi: Tòa án nhân dân quận Hoàn Kiếm",
        # Page 4: Lawsuit Chapter/Article style
        "Chương I. Quan điểm khởi kiện\nĐiều 1. Yêu cầu bồi thường thiệt hại\nCác chi phí phát sinh bao gồm...",
    ]
    
    result = split_and_classify_pdf(mock_pdf_ocr)
    print(json.dumps(result, ensure_ascii=False, indent=2))
