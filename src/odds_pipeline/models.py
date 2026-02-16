from __future__ import annotations
from dataclasses import dataclass
from typing import Optional

@dataclass(frozen=True)
class WideOURecord:
    sportsbook: str
    game: str
    market: str
    player: str
    line: Optional[float]
    odds_over: float
    odds_under: float
    timestamp_ms: Optional[int] = None

@dataclass(frozen=True)
class Offer:
    sportsbook: str
    game: str
    market: str
    player: str
    line: Optional[float]
    selection: str   # OVER / UNDER
    odds: float      # raw odds (american or decimal)
    odds_format: str # "american" or "decimal"
    timestamp_ms: Optional[int] = None
