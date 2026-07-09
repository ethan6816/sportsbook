"""Sports EV model — see sports_ev.pdf for the math this implements."""
from __future__ import annotations

from .odds import american_to_decimal, to_decimal, implied_prob
from .model import (
    devig_proportional,
    fair_prob_from_sharp,
    ev_per_dollar,
    kelly_fraction,
    stake_size,
)
from .normalize import normalize_game, normalize_market, normalize_player, match_key

__all__ = [
    "american_to_decimal",
    "to_decimal",
    "implied_prob",
    "devig_proportional",
    "fair_prob_from_sharp",
    "ev_per_dollar",
    "kelly_fraction",
    "stake_size",
    "normalize_game",
    "normalize_market",
    "normalize_player",
    "match_key",
]
