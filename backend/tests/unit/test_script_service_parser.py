from __future__ import annotations

import pytest

from app.services.script_service import ScriptGenerationError, ScriptService


def test_parses_plain_json() -> None:
    raw = (
        '{"variants": [{"title": "Mở đầu", "body": "Cả nhà ơi", '
        '"estimated_duration_sec": 25, "tags": ["tò mò", "ấm áp"]}]}'
    )
    variants = ScriptService._parse_variants(raw, fallback_duration=30)
    assert len(variants) == 1
    assert variants[0].title == "Mở đầu"
    assert variants[0].estimated_duration_sec == 25
    assert "tò mò" in variants[0].tags


def test_parses_json_wrapped_in_markdown_fence() -> None:
    raw = '```json\n{"variants": [{"title": "X", "body": "Y"}]}\n```'
    out = ScriptService._parse_variants(raw, fallback_duration=30)
    assert out[0].title == "X"
    assert out[0].estimated_duration_sec == 30  # fallback applied


def test_parses_json_with_prose_around() -> None:
    raw = 'Đây là kết quả:\n{"variants":[{"title":"A","body":"B"}]}\nHy vọng phù hợp.'
    out = ScriptService._parse_variants(raw, fallback_duration=20)
    assert out[0].title == "A"


def test_raises_when_no_variants() -> None:
    with pytest.raises(ScriptGenerationError):
        ScriptService._parse_variants('{"variants": []}', fallback_duration=30)


def test_raises_when_no_json() -> None:
    with pytest.raises(ScriptGenerationError):
        ScriptService._parse_variants("không có gì cả", fallback_duration=30)
