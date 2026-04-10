from pathlib import Path

from PIL import Image

from app.services.pdf_exporter import create_searchable_pdf


class _FakePage:
    def __init__(self):
        self.inserted_text = []

    def insert_image(self, rect, filename=None, stream=None):
        _ = (rect, filename, stream)

    def insert_text(self, point, text, fontsize, fontname, render_mode):
        self.inserted_text.append(
            {
                "point": point,
                "text": text,
                "fontsize": fontsize,
                "fontname": fontname,
                "render_mode": render_mode,
            }
        )


class _FakeDoc:
    def __init__(self):
        self.pages = []
        self.saved_path = None

    def new_page(self, width, height):
        _ = (width, height)
        page = _FakePage()
        self.pages.append(page)
        return page

    def save(self, output_path, deflate, garbage=None, clean=None):
        _ = (deflate, garbage, clean)
        self.saved_path = output_path

    def close(self):
        pass


def test_create_searchable_pdf_uses_xywh_bbox(monkeypatch, tmp_path: Path):
    fake_doc = _FakeDoc()
    monkeypatch.setattr("app.services.pdf_exporter.fitz.open", lambda: fake_doc)

    image_path = tmp_path / "page.png"
    Image.new("RGB", (300, 200), "white").save(image_path)
    output_path = tmp_path / "out.pdf"

    pages_data = [
        {
            "input_path": str(image_path),
            "lines": [{"text": "Hello", "bbox": [20, 40, 120, 30], "confidence": 90.0}],
        }
    ]

    create_searchable_pdf(pages_data, str(output_path))
    inserted = fake_doc.pages[0].inserted_text[0]
    # y baseline should be computed from y + h (xywh format), not from y1 in xyxy.
    assert inserted["point"][1] > 40
    assert inserted["render_mode"] == 3
