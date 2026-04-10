from pathlib import Path

from app.services.incremental_learning import (
    apply_incremental_lexicon,
    retrain_incremental_from_feedback,
)


def test_retrain_incremental_builds_lexicon(monkeypatch, tmp_path: Path):
    monkeypatch.setattr(
        "app.services.incremental_learning.get_all_feedback",
        lambda: [
            {"original_text": "Uy dinh", "corrected_text": "Quy dinh"},
            {"original_text": "Uy dinh", "corrected_text": "Quy dinh"},
            {"original_text": "tai chin", "corrected_text": "tai chinh"},
        ],
    )
    model_dir = tmp_path / "models"
    result = retrain_incremental_from_feedback(output_dir=model_dir, min_frequency=2)
    assert result["updated_entries"] == 1
    assert Path(result["lexicon_path"]).exists()


def test_apply_incremental_lexicon_replaces_known_phrase(tmp_path: Path):
    model_dir = tmp_path / "models"
    model_dir.mkdir(parents=True, exist_ok=True)
    lexicon_path = model_dir / "incremental_lexicon.json"
    lexicon_path.write_text('{"uy dinh":"quy dinh"}', encoding="utf-8")

    corrected = apply_incremental_lexicon("Noi dung Uy dinh moi", lexicon_path=lexicon_path)
    assert "quy dinh" in corrected.lower()
