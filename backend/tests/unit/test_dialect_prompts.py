from __future__ import annotations

from app.models.script import Dialect, ScriptIntent
from app.services.dialect_prompts import (
    DIALECT_STYLE,
    INTENT_BRIEF,
    SYSTEM_PROMPT,
    build_user_prompt,
)


def test_system_prompt_is_vietnamese_and_constrained() -> None:
    assert "tiếng Việt" in SYSTEM_PROMPT
    assert "TikTok Shop" in SYSTEM_PROMPT
    # Compliance guard wording must be present
    assert "phóng đại" in SYSTEM_PROMPT


def test_dialects_have_distinct_markers() -> None:
    north = DIALECT_STYLE[Dialect.NORTH]
    south = DIALECT_STYLE[Dialect.SOUTH]
    assert "ạ" in north and "nhé" in north
    assert "nha" in south and "nè" in south
    # No cross-contamination of dialect-specific particles in the guides themselves
    assert "nha" not in north.split("Tránh từ địa phương")[0]


def test_every_intent_has_a_brief() -> None:
    for intent in ScriptIntent:
        assert intent in INTENT_BRIEF
        assert len(INTENT_BRIEF[intent]) > 20


def test_build_user_prompt_includes_context() -> None:
    prompt = build_user_prompt(
        dialect=Dialect.SOUTH,
        intent=ScriptIntent.HOOK,
        product_name="Serum Vitamin C",
        product_category="skincare",
        price_band="under-200k",
        audience_persona="nữ 25-35, da dầu",
        target_duration_sec=30,
        n_variants=3,
    )
    assert "Serum Vitamin C" in prompt
    assert "skincare" in prompt
    assert "under-200k" in prompt
    assert "nữ 25-35" in prompt
    assert "3 biến thể" in prompt
    assert "JSON" in prompt
    # Word target ~ 75 for 30s
    assert "khoảng 75 từ" in prompt or "khoảng 75" in prompt
