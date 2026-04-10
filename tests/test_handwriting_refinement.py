def test_refine_ocr_for_handwriting_graceful_when_model_unavailable(monkeypatch):
    from app.services.handwriting import refine_ocr_for_handwriting

    monkeypatch.setattr(
        "app.services.handwriting._get_trocr_components",
        lambda: (None, None),
    )
    pages = [
        {
            "input_path": "a.png",
            "full_text": "abc",
            "lines": [{"text": "abc", "bbox": [10, 10, 20, 10], "confidence": 40.0}],
        }
    ]
    result = refine_ocr_for_handwriting(pages)
    assert result["applied"] is False
    assert result["pages"][0]["lines"][0]["text"] == "abc"
