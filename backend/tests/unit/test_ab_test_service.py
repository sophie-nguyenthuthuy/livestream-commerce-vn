from __future__ import annotations

from app.services.ab_test_service import VariantStats, evaluate


def test_evaluate_declares_winner_when_large_lift_and_enough_samples() -> None:
    variants = [
        VariantStats(variant_id="A", label="A", impressions=5000, clicks=250),  # 5.0% CTR
        VariantStats(variant_id="B", label="B", impressions=5000, clicks=400),  # 8.0% CTR
    ]
    out = evaluate(variants, min_impressions_per_variant=1000, confidence_target=0.95)

    assert out.has_enough_data is True
    assert out.recommended_winner == "B"
    assert out.decision_confidence > 0.95
    # CTR ordering matches the sample CTR
    b = next(r for r in out.variants if r.label == "B")
    a = next(r for r in out.variants if r.label == "A")
    assert b.ctr > a.ctr
    assert "B" in out.explain


def test_evaluate_waits_when_under_min_samples() -> None:
    variants = [
        VariantStats(variant_id="A", label="A", impressions=200, clicks=10),
        VariantStats(variant_id="B", label="B", impressions=180, clicks=20),
    ]
    out = evaluate(variants, min_impressions_per_variant=1000, confidence_target=0.95)
    assert out.has_enough_data is False
    assert out.recommended_winner is None
    assert "more impressions" in out.explain


def test_evaluate_inconclusive_when_lift_small() -> None:
    # Two nearly identical variants with plenty of data — no clear winner.
    variants = [
        VariantStats(variant_id="A", label="A", impressions=5000, clicks=250),
        VariantStats(variant_id="B", label="B", impressions=5000, clicks=255),
    ]
    out = evaluate(variants, min_impressions_per_variant=1000, confidence_target=0.95)
    assert out.has_enough_data is True
    assert out.recommended_winner is None
    assert out.decision_confidence < 0.95


def test_evaluate_probabilities_sum_to_one() -> None:
    variants = [
        VariantStats(variant_id="A", label="A", impressions=1000, clicks=50),
        VariantStats(variant_id="B", label="B", impressions=1000, clicks=70),
        VariantStats(variant_id="C", label="C", impressions=1000, clicks=60),
    ]
    out = evaluate(variants, min_impressions_per_variant=500, confidence_target=0.95)
    total = sum(r.prob_best for r in out.variants)
    assert abs(total - 1.0) < 1e-6


def test_ci_brackets_observed_ctr() -> None:
    variants = [
        VariantStats(variant_id="A", label="A", impressions=2000, clicks=100),
        VariantStats(variant_id="B", label="B", impressions=2000, clicks=120),
    ]
    out = evaluate(variants, min_impressions_per_variant=500, confidence_target=0.95)
    for r in out.variants:
        assert r.ctr_ci_low <= r.ctr <= r.ctr_ci_high
