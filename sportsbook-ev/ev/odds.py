"""Odds conversions (LaTeX: "Thoughts" and Section 1, Problem).

American odds -> decimal odds -> implied probability.
"""
from __future__ import annotations

import math


def american_to_decimal(a: float) -> float:
    """Convert American odds `a` to decimal odds `d`.

    LaTeX:
        d = 1 + 100/|a|   if a < 0
        d = 1 + a/100     if a > 0

    A $1 bet at decimal odds d returns $d total on a win (stake + (d-1) profit),
    and $0 on a loss.
    """
    a = float(a)
    if math.isnan(a) or a == 0:
        raise ValueError(f"invalid American odds: {a!r}")
    if a < 0:
        return 1.0 + 100.0 / abs(a)
    return 1.0 + a / 100.0


def to_decimal(odds: float, fmt: str) -> float:
    """Convert `odds` in the given format ('american' or 'decimal') to decimal."""
    fmt = str(fmt).lower().strip()
    if fmt == "decimal":
        d = float(odds)
        if d <= 1.0 or math.isnan(d):
            raise ValueError(f"invalid decimal odds: {odds!r}")
        return d
    if fmt == "american":
        return american_to_decimal(float(odds))
    raise ValueError(f"unknown odds_format: {fmt!r}")


def implied_prob(d: float) -> float:
    """Implied probability from decimal odds (LaTeX: p_implied = 1/d)."""
    return 1.0 / d
