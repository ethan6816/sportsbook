from __future__ import annotations

def american_to_decimal(am: float) -> float:
    am = int(am)
    if am == 0:
        raise ValueError("American odds cannot be 0")
    return 1.0 + (am/100.0 if am > 0 else 100.0/abs(am))

def to_decimal(odds: float, fmt: str) -> float:
    fmt = fmt.lower().strip()
    if fmt == "decimal":
        return float(odds)
    if fmt == "american":
        return american_to_decimal(float(odds))
    raise ValueError(f"Unknown odds_format: {fmt}")

def implied_prob_from_decimal(d: float) -> float:
    if d <= 1.0:
        raise ValueError("Decimal odds must be > 1.0")
    return 1.0 / d

def devig_proportional(implied_probs: list[float]) -> list[float]:
    s = sum(implied_probs)
    return [p/s for p in implied_probs]

def ev_per_dollar(p_true: float, d: float) -> float:
    return p_true * (d - 1.0) - (1.0 - p_true)

def kelly_fraction(p_true: float, d: float) -> float:
    b = d - 1.0
    return (b * p_true - (1.0 - p_true)) / b

def stake_size(bankroll: float, p_true: float, d: float, kelly_mult: float, max_frac: float) -> float:
    f = kelly_fraction(p_true, d)
    if f <= 0:
        return 0.0
    f = min(f * kelly_mult, max_frac)
    return bankroll * f
