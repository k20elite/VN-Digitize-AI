import logging
import shutil
import subprocess
from io import BytesIO
from pathlib import Path
import fitz  # PyMuPDF
from PIL import Image

logger = logging.getLogger(__name__)


def _render_page_image(path: str, mrc_compression: bool) -> bytes:
    with Image.open(path) as image:
        if not mrc_compression:
            stream = BytesIO()
            image.save(stream, format="PNG")
            return stream.getvalue()

        # MRC-like simplification: keep text edges sharp but reduce photographic
        # background entropy by composing grayscale base + enhanced foreground.
        grayscale = image.convert("L")
        fg_mask = grayscale.point(lambda p: 255 if p < 180 else 0)
        fg = image.copy()
        fg.putalpha(fg_mask)
        base = grayscale.convert("RGB")
        base.paste(fg.convert("RGB"), mask=fg_mask)
        stream = BytesIO()
        base.save(stream, format="JPEG", quality=75, optimize=True)
        return stream.getvalue()


def _convert_to_pdfa_if_available(
    src_path: str,
    *,
    pdfa_level: str,
    strict: bool,
) -> tuple[bool, str | None, str]:
    gs_binary = shutil.which("gswin64c") or shutil.which("gs")
    if not gs_binary:
        warning = "PDF/A converter (Ghostscript) is unavailable."
        if strict:
            raise RuntimeError(warning)
        return False, warning, src_path

    out_path = str(Path(src_path).with_suffix(".pdfa.pdf"))
    compatibility = "1.4" if pdfa_level == "1b" else "1.7"
    command = [
        gs_binary,
        "-dBATCH",
        "-dNOPAUSE",
        "-dSAFER",
        f"-dPDFA={1 if pdfa_level == '1b' else 2}",
        f"-dCompatibilityLevel={compatibility}",
        "-sProcessColorModel=DeviceRGB",
        "-sDEVICE=pdfwrite",
        f"-sOutputFile={out_path}",
        src_path,
    ]
    try:
        subprocess.run(command, check=True, capture_output=True, text=True)
    except Exception as exc:
        warning = f"PDF/A conversion failed: {exc}"
        if strict:
            raise RuntimeError(warning) from exc
        return False, warning, src_path
    return True, None, out_path


def export_searchable_pdf(
    pages_data: list[dict],
    output_path: str,
    *,
    pdfa_level: str | None = "2b",
    mrc_compression: bool = True,
    strict_pdfa: bool = False,
) -> dict:
    warnings: list[str] = []
    """
    Creates a searchable PDF/A-like file by overlaying OCR text as an invisible layer 
    on top of the original images.
    
    pages_data is expected to be a list of dictionaries, each resembling an OCRPageResult:
    {
        "input_path": str,
        "lines": [
            {"text": str, "bbox": [x, y, w, h], "confidence": float}, ...
        ]
    }
    """
    doc = fitz.open()

    # Create a basic font for unicode (searchable layer)
    # PyMuPDF's built-in Helvetica might lack some Vietnamese accents, 
    # but works reasonably well for basic searchable background layer overlay.
    
    for page_info in pages_data:
        img_path = page_info.get("input_path")
        lines = page_info.get("lines", [])

        if not img_path or not Path(img_path).exists():
            logger.warning(f"Image not found for PDF export: {img_path}")
            continue

        # Get image dimensions to set page size
        try:
            with Image.open(img_path) as im:
                width, height = im.size
        except Exception as e:
            logger.warning(f"Error reading image dimensions for {img_path}: {str(e)}")
            continue

        # Create a new PDF page with the same dimensions
        page = doc.new_page(width=width, height=height)

        # 1. Overlay the scanned image as the background
        rect = fitz.Rect(0, 0, width, height)
        page.insert_image(rect, stream=_render_page_image(img_path, mrc_compression))

        # 2. Add invisible text layer based on OCR lines
        for line in lines:
            text = line.get("text", "")
            if not text:
                continue

            bbox = line.get("bbox", [])
            if len(bbox) != 4:
                continue

            x0, y0, line_width, line_height = bbox

            if line_width <= 0 or line_height <= 0:
                continue

            # Approximate font size to fit the bounding box height
            fontsize = line_height * 0.8
            # Render_mode = 3 means invisible text (stroke and fill not painted)
            try:
                page.insert_text(
                    (x0, y0 + line_height - (line_height * 0.2)), # Baseline estimation
                    text,
                    fontsize=fontsize,
                    fontname="helv",
                    render_mode=3
                )
            except Exception:
                # If unicode fails with basic font, it silently skips that specific line's visibility layer
                pass

    doc.save(output_path, deflate=True, garbage=4, clean=True)
    doc.close()

    pdfa_compliant = False
    final_path = output_path
    if pdfa_level:
        compliant, warning, maybe_path = _convert_to_pdfa_if_available(
            output_path,
            pdfa_level=pdfa_level,
            strict=strict_pdfa,
        )
        pdfa_compliant = compliant
        final_path = maybe_path
        if warning:
            warnings.append(warning)

    return {
        "output_path": final_path,
        "pdfa_compliant": pdfa_compliant,
        "compression": "mrc-like" if mrc_compression else "deflate",
        "warnings": warnings,
    }


def create_searchable_pdf(pages_data: list[dict], output_path: str) -> str:
    result = export_searchable_pdf(
        pages_data=pages_data,
        output_path=output_path,
        pdfa_level=None,
        mrc_compression=False,
        strict_pdfa=False,
    )
    return str(result["output_path"])
