"""Generate +EV betting signals from the merged offers feed.

Pipeline (mirrors sports_ev.pdf):
  1. Convert every price to decimal odds, then implied probability.
  2. For the sharp book, de-vig each two-sided (Over/Under) market -> fair prob.
  3. For every OTHER book offering the same bet, compute EV with that fair prob.
  4. Keep bets above --min-ev, size each with fractional capped Kelly.

Cross-book matching uses normalized game/market/player keys with an exact line,
so books that name things differently still line up on the same bet.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from ev import (  # noqa: E402
    to_decimal,
    implied_prob,
    fair_prob_from_sharp,
    ev_per_dollar,
    stake_size,
    normalize_game,
    normalize_market,
    normalize_player,
)


def _best_price(rows: pd.DataFrame) -> pd.Series:
    """Best (highest) decimal price row for a side."""
    return rows.sort_values("odds_decimal", ascending=False).iloc[0]


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--offers", default=str(ROOT / "data" / "offers_long.csv"))
    ap.add_argument("--sharp", default="fanduel", help="book treated as the sharp reference")
    ap.add_argument("--bankroll", type=float, default=1000.0)
    ap.add_argument("--min-ev", type=float, default=0.01, help="minimum EV per $1 staked")
    ap.add_argument("--kelly-mult", type=float, default=0.25, help="fractional Kelly multiplier")
    ap.add_argument("--max-frac", type=float, default=0.02, help="max stake as fraction of bankroll")
    ap.add_argument("--out", default=str(ROOT / "data" / "signals.csv"))
    args = ap.parse_args()

    offers_path = Path(args.offers)
    if not offers_path.exists():
        raise SystemExit(f"Missing offers file: {offers_path}. Run scripts/build_offers.py first.")

    df = pd.read_csv(offers_path)
    req = {"sportsbook", "game", "market", "player", "line", "selection", "odds", "odds_format"}
    missing = req - set(df.columns)
    if missing:
        raise SystemExit(f"Offers file missing columns: {missing}")

    # decimal odds + normalized matching keys
    df["odds_decimal"] = df.apply(lambda r: to_decimal(r["odds"], r["odds_format"]), axis=1)
    df["gk"] = df["game"].map(normalize_game)
    df["mk"] = df.apply(lambda r: normalize_market(r["market"]), axis=1)
    df["pk"] = df.apply(lambda r: normalize_player(r["player"], r["market"]), axis=1)
    df["lk"] = pd.to_numeric(df["line"], errors="coerce").round(1)
    df["selection"] = df["selection"].str.upper().str.strip()

    sharp = df[df["sportsbook"] == args.sharp].copy()
    other = df[df["sportsbook"] != args.sharp].copy()
    if sharp.empty:
        raise SystemExit(f"No rows for sharp book '{args.sharp}'.")
    if other.empty:
        raise SystemExit("No non-sharp books to compare against.")

    key_cols = ["gk", "mk", "pk", "lk"]
    # index other-book offers by (key, selection) for fast lookup
    other_idx: dict[tuple, pd.DataFrame] = {k: g for k, g in other.groupby(key_cols)}

    signals = []
    for key, g in sharp.groupby(key_cols):
        sides = set(g["selection"].unique())
        if not {"OVER", "UNDER"} <= sides:
            continue  # need both sides on the sharp book to de-vig

        d_over = float(_best_price(g[g["selection"] == "OVER"])["odds_decimal"])
        d_under = float(_best_price(g[g["selection"] == "UNDER"])["odds_decimal"])
        p_over, p_under = fair_prob_from_sharp(d_over, d_under)

        g_other = other_idx.get(key)
        if g_other is None or g_other.empty:
            continue

        for sel, p_true, d_sharp in (("OVER", p_over, d_over), ("UNDER", p_under, d_under)):
            side = g_other[g_other["selection"] == sel]
            if side.empty:
                continue
            row = _best_price(side)
            d = float(row["odds_decimal"])
            ev = ev_per_dollar(p_true, d)
            if ev < args.min_ev:
                continue
            stake = stake_size(args.bankroll, p_true, d, args.kelly_mult, args.max_frac)
            if stake <= 0:
                continue
            signals.append({
                "sharp_book": args.sharp,
                "sportsbook": row["sportsbook"],
                "game": row["game"],
                "market": row["market"],
                "player": row["player"],
                "line": row["line"],
                "selection": sel,
                "sharp_odds_decimal": round(d_sharp, 4),
                "book_odds_decimal": round(d, 4),
                "p_true": round(p_true, 4),
                "ev_per_$": round(ev, 4),
                "suggested_stake": round(stake, 2),
            })

    out = pd.DataFrame(signals)
    if len(out):
        out = out.sort_values("ev_per_$", ascending=False).reset_index(drop=True)
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(args.out, index=False)
    print(f"Wrote {args.out} with {len(out)} signals")
    if len(out):
        print(out.head(25).to_string(index=False))


if __name__ == "__main__":
    main()
