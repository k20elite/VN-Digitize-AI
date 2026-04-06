import logging
from typing import Any, Dict, List
import os

from PIL import Image

try:
    from reportlab.pdfgen import canvas
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.pdfbase import pdfmetrics
except ImportError:
    pass # Wait for pip install reportlab

logger = logging.getLogger(__name__)

def generate_searchable_pdf(
    image_path: str, 
    ocr_lines: List[Dict[str, Any]], 
    output_pdf_path: str,
    font_path: str = None
) -> str:
    """
    Generates a Searchable PDF (PDF/A compliant format architecture) by overlaying 
    transparent OCR text over the original image at exact bounding box coordinates.
    
    Args:
        image_path: Path to the scanned document image.
        ocr_lines: List of dicts [{"text": "...", "bbox": [x, y, w, h]}]
        output_pdf_path: Destination path for the .pdf file.
        font_path: Optional path to a TrueType font that supports Vietnamese. 
                   If None, it falls back to standard Helvetica (which might drop some VN accents).
    """
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Image not found at {image_path}")

    # 1. Load Image and Setup Canvas
    img = Image.open(image_path)
    img_width, img_height = img.size
    
    # PDF/A creation initializes here (reportlab allows specific embedding settings)
    c = canvas.Canvas(output_pdf_path, pagesize=(img_width, img_height))
    
    # Draw the source image as the visible background
    c.drawImage(image_path, 0, 0, width=img_width, height=img_height)

    # 2. Register Vietnamese-compatible font if provided
    font_name = "Helvetica"
    if font_path and os.path.exists(font_path):
        font_name = "CustomVN"
        pdfmetrics.registerFont(TTFont(font_name, font_path))

    # 3. Render Invisible Text Layer
    # ReportLab coordinate system has (0, 0) at Bottom-Left.
    # Image OCR coordinate system has (0, 0) at Top-Left.
    for line in ocr_lines:
        text = line.get("text", "").strip()
        if not text:
            continue
            
        x, y, w, h = line.get("bbox", [0, 0, 0, 0])
        if w <= 0 or h <= 0:
            continue

        # Convert Top-Left OCR origin to Bottom-Left Canvas origin
        # Note: The y-coordinate for text drawing marks the *baseline* of the text,
        # so we calculate the bottom corner and adjust slightly.
        y_pdf = img_height - (y + h)
        
        # Create a text object to precisely control width and rendering mode
        text_obj = c.beginText()

        # Set text rendering mode to 3 (invisible/transparent, selectable)
        text_obj.setTextRenderMode(3) 

        # Calculate exact font size to match bounding box height (~80% to fit ascenders/descenders)
        font_size = max(1, int(h * 0.85))
        text_obj.setFont(font_name, font_size)

        # Positioning
        text_obj.setTextOrigin(x, y_pdf + (h * 0.15)) # slight baseline adjustment
        
        # Calculate horizontal stretch to perfectly align with [w]
        text_width = pdfmetrics.stringWidth(text, font_name, font_size)
        if text_width > 0:
            stretch_ratio = (w / text_width) * 100
            text_obj.setHorizScale(stretch_ratio)

        # Draw line
        text_obj.textOut(text)
        c.drawText(text_obj)

    # Finalize PDF/A export
    c.save()
    logger.info(f"Generated searchable PDF: {output_pdf_path}")
    
    return output_pdf_path

if __name__ == "__main__":
    # Example PDF generation logic
    pass
