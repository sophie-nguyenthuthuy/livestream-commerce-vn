"""
A/B test analytics for thumbnail variants.

We treat each variant's CTR as a Beta-Bernoulli process:
    successes = clicks, failures = (impressions - clicks)
    posterior  = Beta(alpha + clicks, beta + impressions - clicks)
We use a weakly informative prior Beta(1, 1) (= Uniform) by default.

Two outputs:
    1. 95% credible interval per variant (frequentist-looking, Bayesian-derived).
    2. Probability that each variant is the best ("prob_best"), computed by
       Monte Carlo sampling from each posterior.

A winner is declared when:
    * every variant has >= min_impressions_per_variant samples, AND
    * the leader's prob_best >= confidence_target.

This avoids the classic mistake of declaring winners on the first 100 clicks.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

import numpy as np
from scipy import stats


@dataclass(frozen=True)
class VariantStats:
    variant_id: str
    label: str
    impressions: int
    clicks: int


@dataclass(frozen=True)
class VariantResult:
    variant_id: str
    label: str
    impressions: int
    clicks: int
    ctr: float
    ctr_ci_low: float
    ctr_ci_high: float
    prob_best: float


@dataclass(frozen=True)
class TestEvaluation:
    variants: list[VariantResult]
    has_enough_data: bool
    recommended_winner: str | None
    decision_confidence: float
    explain: str


_PRIOR_ALPHA = 1.0
_PRIOR_BETA = 1.0
_MC_SAMPLES = 20_000
_RNG = np.random.default_rng(seed=42)


def evaluate(
    variants: Sequence[VariantStats],
    *,
    min_impressions_per_variant: int,
    confidence_target: float,
) -> TestEvaluation:
    if len(variants) < 2:
        raise ValueError("need at least 2 variants to evaluate")

    # Posterior samples per variant: shape (n_variants, MC_SAMPLES)
    samples = np.vstack(
        [
            _RNG.beta(
                _PRIOR_ALPHA + v.clicks,
                _PRIOR_BETA + max(v.impressions - v.clicks, 0),
                size=_MC_SAMPLES,
            )
            for v in variants
        ]
    )
    # P(variant is best) = fraction of MC draws where variant has the max CTR
    best_idx = np.argmax(samples, axis=0)
    counts = np.bincount(best_idx, minlength=len(variants))
    prob_best = counts / _MC_SAMPLES

    results: list[VariantResult] = []
    for i, v in enumerate(variants):
        if v.impressions > 0:
            ctr = v.clicks / v.impressions
            ci_low, ci_high = stats.beta.interval(
                0.95,
                _PRIOR_ALPHA + v.clicks,
                _PRIOR_BETA + max(v.impressions - v.clicks, 0),
            )
        else:
            ctr = 0.0
            ci_low, ci_high = 0.0, 1.0
        results.append(
            VariantResult(
                variant_id=v.variant_id,
                label=v.label,
                impressions=v.impressions,
                clicks=v.clicks,
                ctr=ctr,
                ctr_ci_low=float(ci_low),
                ctr_ci_high=float(ci_high),
                prob_best=float(prob_best[i]),
            )
        )

    has_enough = all(v.impressions >= min_impressions_per_variant for v in variants)
    leader = max(results, key=lambda r: r.prob_best)

    if has_enough and leader.prob_best >= confidence_target:
        winner = leader.variant_id
        confidence = leader.prob_best
        runner_up = max(
            (r for r in results if r.variant_id != winner),
            key=lambda r: r.prob_best,
        )
        lift = (
            (leader.ctr - runner_up.ctr) / runner_up.ctr * 100
            if runner_up.ctr > 0
            else float("inf")
        )
        explain = (
            f"Variant '{leader.label}' is best with P={leader.prob_best:.1%} "
            f"(CTR {leader.ctr:.2%} vs '{runner_up.label}' {runner_up.ctr:.2%}, "
            f"lift {lift:+.1f}%)."
        )
    else:
        winner = None
        confidence = leader.prob_best
        if not has_enough:
            shortest = min(variants, key=lambda v: v.impressions)
            need = min_impressions_per_variant - shortest.impressions
            explain = (
                f"Not enough data yet — variant '{shortest.label}' needs "
                f"{need} more impressions to reach the minimum "
                f"of {min_impressions_per_variant}."
            )
        else:
            explain = (
                f"Inconclusive: leader '{leader.label}' has only "
                f"P={leader.prob_best:.1%} of being best, "
                f"below target {confidence_target:.0%}. Keep running."
            )

    return TestEvaluation(
        variants=results,
        has_enough_data=has_enough,
        recommended_winner=winner,
        decision_confidence=float(confidence),
        explain=explain,
    )
