"""The EV model (LaTeX: Section 1.1 de-vig, Section 2 Kelly).

Given a sharp book's two-sided price, remove the vig proportionally to get a
fair probability, compute EV of another book's price, and size with fractional
capped Kelly.
"""
from __future__ import annotations

from .odds import implied_prob


def devig_proportional(p_over_imp: float, p_under_imp: float) -> tuple[float, float]:
    """Proportional de-vig (LaTeX Section 1.1).

        p_over  = p_over_imp  / (p_over_imp + p_under_imp)
        p_under = p_under_imp / (p_over_imp + p_under_imp)

    Distributes the book's edge proportionally so the two sides sum to 1.
    """
    s = p_over_imp + p_under_imp
    if s <= 0:
        raise ValueError("implied probabilities must be positive")
    return p_over_imp / s, p_under_imp / s


def fair_prob_from_sharp(d_over: float, d_under: float) -> tuple[float, float]:
    """Fair (de-vigged) Over/Under probabilities from the sharp book's decimal odds."""
    return devig_proportional(implied_prob(d_over), implied_prob(d_under))


def ev_per_dollar(p_true: float, d: float) -> float:
    """Expected profit per $1 staked (LaTeX: EV = p*(d-1) - (1-p)*1)."""
    return p_true * (d - 1.0) - (1.0 - p_true)


def kelly_fraction(p_true: float, d: float) -> float:
    """Full-Kelly fraction of bankroll (LaTeX Section 2).

        b = d - 1
        f* = (p*b - (1 - p)) / b
    """
    b = d - 1.0
    if b <= 0:
        return 0.0
    return (p_true * b - (1.0 - p_true)) / b


def stake_size(
    bankroll: float,
    p_true: float,
    d: float,
    kelly_mult: float = 0.25,
    max_frac: float = 0.02,
) -> float:
    """Recommended stake in dollars.

    LaTeX Section 2: use fractional Kelly (a quarter of f*) and cap the stake at
    a fixed fraction of bankroll, because f* assumes the fair-probability
    estimate is exact and de-vigging is only an approximation.
    """
    f = kelly_fraction(p_true, d)
    if f <= 0:
        return 0.0
    f = min(f * kelly_mult, max_frac)
    return bankroll * f
