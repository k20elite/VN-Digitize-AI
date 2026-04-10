from pathlib import Path

import cv2
import numpy as np

from app.schemas import PreprocessOptions
from app.services.preprocessing import (
    deskew_image,
    estimate_skew_angle,
    is_blank_page,
    preprocess_image,
    run_preprocess_pipeline,
)


def test_is_blank_page_detects_white_page():
    image = np.full((300, 200, 3), 255, dtype=np.uint8)
    assert is_blank_page(image, threshold=0.01)


def test_preprocess_pipeline_skips_blank_page(tmp_path: Path):
    image = np.full((300, 200, 3), 255, dtype=np.uint8)
    input_path = tmp_path / "blank.png"
    cv2.imwrite(str(input_path), image)

    options = PreprocessOptions(remove_blank_pages=True)
    results = run_preprocess_pipeline([str(input_path)], tmp_path / "out", options)

    assert len(results) == 1
    assert results[0]["skipped_as_blank"] is True
    assert results[0]["output_path"] is None


def test_preprocess_pipeline_outputs_clean_file(tmp_path: Path):
    image = np.full((300, 300, 3), 255, dtype=np.uint8)
    cv2.rectangle(image, (50, 100), (250, 150), (0, 0, 0), thickness=-1)
    input_path = tmp_path / "content.png"
    cv2.imwrite(str(input_path), image)

    options = PreprocessOptions(remove_blank_pages=True)
    results = run_preprocess_pipeline([str(input_path)], tmp_path / "out", options)

    assert len(results) == 1
    assert results[0]["skipped_as_blank"] is False
    assert results[0]["output_path"] is not None
    assert Path(results[0]["output_path"]).exists()


def _create_synthetic_text_image() -> np.ndarray:
    image = np.full((400, 600, 3), 255, dtype=np.uint8)
    for y in [90, 150, 210, 270, 330]:
        cv2.line(image, (70, y), (530, y), (0, 0, 0), 3)
    return image


def _rotate_image(image: np.ndarray, angle: float) -> np.ndarray:
    h, w = image.shape[:2]
    matrix = cv2.getRotationMatrix2D((w // 2, h // 2), angle, 1.0)
    return cv2.warpAffine(
        image,
        matrix,
        (w, h),
        flags=cv2.INTER_CUBIC,
        borderMode=cv2.BORDER_REPLICATE,
    )


def test_estimate_skew_angle_detects_rotated_text():
    base = _create_synthetic_text_image()
    rotated = _rotate_image(base, 12.0)
    estimated = estimate_skew_angle(rotated)
    assert abs(abs(estimated) - 12.0) < 2.0


def test_deskew_image_reduces_skew():
    base = _create_synthetic_text_image()
    rotated = _rotate_image(base, 12.0)
    corrected = deskew_image(rotated)

    before = abs(estimate_skew_angle(rotated))
    after = abs(estimate_skew_angle(corrected))

    assert before > 5.0
    assert after < 1.5


def test_binarize_preserves_red_stamp_pixels():
    image = np.full((220, 220, 3), 255, dtype=np.uint8)
    cv2.rectangle(image, (30, 30), (110, 110), (0, 0, 255), thickness=-1)
    cv2.putText(image, "A1", (130, 130), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)

    options = PreprocessOptions(
        deskew=False,
        auto_crop=False,
        shadow_removal=False,
        denoise=False,
        remove_yellow_stains=False,
        binarize=True,
        preserve_red_stamp=True,
        remove_blank_pages=False,
    )
    processed = preprocess_image(image, options)
    red_mask = (processed[:, :, 2] > 180) & (processed[:, :, 1] < 120)
    assert int(np.count_nonzero(red_mask)) > 300


<<<<<<< HEAD
def test_binarize_preserves_red_stamp_with_denoise_enabled():
    image = np.full((260, 260, 3), 255, dtype=np.uint8)
    # Stamp-like red ring with small noisy border to simulate real scan.
    cv2.circle(image, (130, 130), 45, (0, 0, 220), thickness=4)
    noise = np.random.default_rng(7).integers(0, 20, size=image.shape, dtype=np.uint8)
    image = cv2.subtract(image, noise)

    options = PreprocessOptions(
        deskew=False,
        auto_crop=False,
        shadow_removal=False,
        denoise=True,
        remove_yellow_stains=False,
        binarize=True,
        preserve_red_stamp=True,
        remove_blank_pages=False,
    )
    processed = preprocess_image(image, options)
    red_mask = (processed[:, :, 2] > 150) & (processed[:, :, 1] < 140)
    assert int(np.count_nonzero(red_mask)) > 120


def test_preserve_red_stamp_uses_pre_denoise_reference(monkeypatch):
    image = np.full((180, 180, 3), 255, dtype=np.uint8)
    cv2.rectangle(image, (50, 50), (120, 120), (0, 0, 220), thickness=-1)

    # Simulate an aggressive denoise implementation that wipes color cues.
    monkeypatch.setattr(
        "app.services.preprocessing.denoise_image",
        lambda img: np.full_like(img, 255),
    )

    options = PreprocessOptions(
        deskew=False,
        auto_crop=False,
        shadow_removal=False,
        denoise=True,
        remove_yellow_stains=False,
        binarize=True,
        preserve_red_stamp=True,
        remove_blank_pages=False,
    )
    processed = preprocess_image(image, options)
    red_mask = (processed[:, :, 2] > 150) & (processed[:, :, 1] < 140)
    assert int(np.count_nonzero(red_mask)) > 200


=======
>>>>>>> fa883a38ced3be0325d8d4a97f8c1c11e446b43c
def test_shadow_removal_flattens_background():
    h, w = 260, 260
    x = np.linspace(40, 210, w, dtype=np.float32)
    gradient = np.tile(x, (h, 1))
    image = np.stack([gradient, gradient, gradient], axis=2).astype(np.uint8)
    cv2.putText(image, "TXT", (60, 150), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 0, 0), 3)

    options = PreprocessOptions(
        deskew=False,
        auto_crop=False,
        shadow_removal=True,
        denoise=False,
        remove_yellow_stains=False,
        binarize=False,
        remove_blank_pages=False,
    )
    processed = preprocess_image(image, options)

    original_gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    processed_gray = cv2.cvtColor(processed, cv2.COLOR_BGR2GRAY)
    assert float(np.std(processed_gray)) < float(np.std(original_gray))
<<<<<<< HEAD


def test_preprocess_image_applies_deskew_when_enabled(monkeypatch):
    image = np.full((120, 160, 3), 255, dtype=np.uint8)
    calls = {"deskew": 0}

    def fake_deskew(img):
        calls["deskew"] += 1
        return img

    monkeypatch.setattr("app.services.preprocessing.deskew_image", fake_deskew)
    options = PreprocessOptions(
        deskew=True,
        auto_crop=False,
        shadow_removal=False,
        denoise=False,
        remove_yellow_stains=False,
        binarize=False,
        remove_blank_pages=False,
    )
    _ = preprocess_image(image, options)
    assert calls["deskew"] == 1
=======
>>>>>>> fa883a38ced3be0325d8d4a97f8c1c11e446b43c
