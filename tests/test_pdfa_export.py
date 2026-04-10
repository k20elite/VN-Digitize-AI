from pathlib import Path

from PIL import Image

from app.services.pdf_exporter import export_searchable_pdf


def test_export_searchable_pdf_reports_pdfa_unavailable(monkeypatch, tmp_path: Path):
    image_path = tmp_path / "page.png"
    Image.new("RGB", (200, 120), "white").save(image_path)
    out_path = tmp_path / "out.pdf"

    monkeypatch.setattr(
        "app.services.pdf_exporter._convert_to_pdfa_if_available",
        lambda src_path, pdfa_level, strict: (False, "converter unavailable", src_path),
    )
    result = export_searchable_pdf(
        pages_data=[{"input_path": str(image_path), "lines": []}],
        output_path=str(out_path),
        pdfa_level="2b",
        mrc_compression=True,
        strict_pdfa=False,
    )
    assert result["output_path"].endswith(".pdf")
    assert result["pdfa_compliant"] is False
    assert result["compression"].startswith("mrc")
