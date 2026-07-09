"""Cross-book normalization so the same bet lines up across sportsbooks.

Each book names things differently:
    game    fanduel: 'phoenix-suns-@-minnesota-timberwolves-35036256'
            betmgm:  'phoenix-suns-at-minnesota-timberwolves'
            prophetx:'phoenix-suns-vs-minnesota-timberwolves'
    market  fanduel/betmgm: 'points rebounds assists'   prophetx: 'points ou'
    player  prophetx appends the stat: 'Dillon Brooks Points'

Without normalizing these, an exact join finds zero matches and the model never
emits a signal. We normalize game/market/player to a canonical key; the numeric
`line` must still match exactly, because Over 28.5 and Over 27.5 are different
bets and only the same bet can be compared.
"""
from __future__ import annotations

import re

# stat tokens that make up a market, and the filler words books add
_STAT_WORDS = {
    "points": "points",
    "point": "points",
    "pts": "points",
    "rebounds": "rebounds",
    "rebound": "rebounds",
    "rebs": "rebounds",
    "reb": "rebounds",
    "assists": "assists",
    "assist": "assists",
    "ast": "assists",
    "threes": "threes",
    "three": "threes",
    "pointers": None,      # 'three pointers' -> threes (handled with 'three')
    "3pt": "threes",
    "pra": "__pra__",      # expanded below
}
_FILLER = {"ou", "o/u", "player", "nba", "prop", "props", "total", "totals", "made"}
_NAME_SUFFIXES = {"jr", "sr", "ii", "iii", "iv", "v"}


def normalize_game(game: str) -> tuple[str, ...]:
    """Return the game as an order-independent pair of team slugs."""
    g = str(game).strip().lower()
    g = re.sub(r"-\d{4,}$", "", g)                 # drop trailing event id
    g = re.sub(r"\s+", "-", g)
    g = g.replace("-@-", "|").replace("-vs-", "|").replace("-at-", "|")
    g = g.replace("@", "|").replace("-v-", "|")
    parts = [p.strip("-") for p in g.split("|") if p.strip("-")]
    return tuple(sorted(parts))


def normalize_market(market: str) -> str:
    """Return a canonical market key, e.g. 'points+rebounds+assists' or 'points'."""
    m = str(market).strip().lower()
    m = m.replace("three pointers", "threes").replace("three-pointers", "threes")
    tokens: list[str] = []
    for raw in re.split(r"[\s_/+-]+", m):
        if not raw or raw in _FILLER:
            continue
        mapped = _STAT_WORDS.get(raw)
        if mapped is None:
            continue
        if mapped == "__pra__":
            tokens.extend(["points", "rebounds", "assists"])
        else:
            tokens.append(mapped)
    canon = sorted(set(tokens))
    return "+".join(canon) if canon else m


def normalize_player(player: str, market: str = "") -> str:
    """Return a canonical player key: strip appended stat words, punctuation, suffixes."""
    p = str(player).strip().lower()
    # strip a trailing stat descriptor that some books append (e.g. 'Dillon Brooks Points')
    p = re.sub(r"\b(points?|rebounds?|assists?|threes?|three\s+pointers?|pra)\b", " ", p)
    p = re.sub(r"[^a-z\s]", "", p)                 # drop punctuation (O'Neale -> oneale)
    words = [w for w in p.split() if w and w not in _NAME_SUFFIXES]
    return "".join(words)


def match_key(game: str, market: str, player: str, line: float) -> tuple:
    """Full cross-book key for one selection's market (line kept exact)."""
    return (
        normalize_game(game),
        normalize_market(market),
        normalize_player(player, market),
        round(float(line), 1),
    )
