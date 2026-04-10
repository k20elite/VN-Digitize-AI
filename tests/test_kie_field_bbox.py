from app.services.kie_field_bbox import map_kie_fields_to_bboxes


def _field(value: str | None, confidence: float = 0.9) -> dict:
    return {"value": value, "confidence": confidence}


def test_map_kie_fields_to_bboxes_matches_core_fields():
    kie_result = {
        "so_van_ban": _field("123/2026/QD-UBND"),
        "ngay_ban_hanh": _field("ngay 05 thang 04 nam 2026"),
        "co_quan_ban_hanh": _field("UBND TP HA NOI"),
        "loai_van_ban": _field("Quyet dinh"),
        "trich_yeu": _field("phe duyet du an"),
        "custom_fields": {},
    }
    lines = [
        {"text": "UBND TP HA NOI", "bbox": [10, 10, 130, 22], "confidence": 96.0},
        {"text": "So: 123/2026/QD-UBND", "bbox": [10, 40, 180, 22], "confidence": 93.0},
        {
            "text": "Ha Noi, ngay 05 thang 04 nam 2026",
            "bbox": [10, 70, 260, 22],
            "confidence": 92.0,
        },
        {"text": "QUYET DINH", "bbox": [10, 100, 120, 22], "confidence": 95.0},
        {"text": "Ve viec phe duyet du an", "bbox": [10, 130, 220, 22], "confidence": 91.0},
    ]

    field_bboxes = map_kie_fields_to_bboxes(kie_result, lines)

    assert field_bboxes["so_van_ban"] == [10, 40, 180, 22]
    assert field_bboxes["ngay_ban_hanh"] == [10, 70, 260, 22]
    assert field_bboxes["co_quan_ban_hanh"] == [10, 10, 130, 22]
    assert field_bboxes["loai_van_ban"] == [10, 100, 120, 22]
    assert field_bboxes["trich_yeu"] == [10, 130, 220, 22]


def test_map_kie_fields_to_bboxes_supports_custom_fields():
    kie_result = {
        "so_van_ban": _field(None, 0.0),
        "ngay_ban_hanh": _field(None, 0.0),
        "co_quan_ban_hanh": _field(None, 0.0),
        "loai_van_ban": _field(None, 0.0),
        "trich_yeu": _field(None, 0.0),
        "custom_fields": {
            "so_ho_so": _field("HS-2026-0001", 0.85),
        },
    }
    lines = [
        {"text": "Ho so: HS-2026-0001", "bbox": [12, 88, 190, 20], "confidence": 90.0},
    ]

    field_bboxes = map_kie_fields_to_bboxes(kie_result, lines)
    assert field_bboxes["so_ho_so"] == [12, 88, 190, 20]
