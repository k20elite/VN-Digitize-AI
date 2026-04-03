from app.services.ocr import _parse_tesseract_tsv


def test_parse_tesseract_tsv_skips_malformed_rows():
    tsv = "\n".join(
        [
            "level\tpage_num\tblock_num\tpar_num\tline_num\tword_num\tleft\ttop\twidth\theight\tconf\ttext",
            "5\t1\t1\t1\t1\t1\t10\t10\t30\t12\t92.0\tXin",
            "5\t1\t1\t1\t1\t2\t45\t10\t25\t12\t88.0\tchao",
            "5\t1\t1\t2\t1\t1\t10\t30\t35\t12\t87.0\tKhong\"",
            "5\t1\t1\t2\t1\t2\t50\t30\t20\t12\t85.0\ttot",
            "garbage-without-tabs",
            "5\t1\t1\t3\t1\t1\ta\t1\t1\t1\t80.0\tbad-number",
        ]
    )

    lines = _parse_tesseract_tsv(tsv)
    assert len(lines) == 2
    assert lines[0]["text"] == "Xin chao"
    assert lines[1]["text"] == 'Khong" tot'
