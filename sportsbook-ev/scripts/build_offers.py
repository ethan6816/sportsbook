"""Merge each book's wide Odds/*.csv into one long offers feed.

Input schema (per book):  game,market,player,line,odds_over,odds_under
Output (data/offers_long.csv): sportsbook,game,market,player,line,selection,odds,odds_format
Rows with missing/invalid over or under prices are dropped here so the model
never sees a half-priced market.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]

ODDS_FILES = {
    "fanduel": ROOT / "Odds" / "fanduel_odds.csv",
    "betmgm": ROOT / "Odds" / "betmgm_nba.csv",
    "prophetx": ROOT / "Odds" / "prophetx_nba.csv",
}

REQUIRED = {"game", "market", "player", "line", "odds_over", "odds_under"}


def wide_to_long(df: pd.DataFrame, sportsbook: str) -> pd.DataFrame:
    missing = REQUIRED - set(df.columns)
    if missing:
        raise ValueError(f"{sportsbook}: missing columns {missing}")

    df = df.copy()
    # keep only rows where BOTH sides have a usable American price (not blank/0)
    for col in ("odds_over", "odds_under"):
        df[col] = pd.to_numeric(df[col], errors="coerce")
    n0 = len(df)
    df = df[(df["odds_over"].notna()) & (df["odds_under"].notna())]
    df = df[(df["odds_over"] != 0) & (df["odds_under"] != 0)]
    df = df[pd.to_numeric(df["line"], errors="coerce").notna()]
    dropped = n0 - len(df)
    if dropped:
        print(f"  {sportsbook}: dropped {dropped} rows with missing/invalid prices")

    base = df[["game", "market", "player", "line"]].copy()
    base["sportsbook"] = sportsbook
    base["odds_format"] = "american"

    over = base.copy()
    over["selection"] = "OVER"
    over["odds"] = df["odds_over"].astype(float).values

    under = base.copy()
    under["selection"] = "UNDER"
    under["odds"] = df["odds_under"].astype(float).values

    return pd.concat([over, under], ignore_index=True)


def main() -> None:
    out_dir = ROOT / "data"
    out_dir.mkdir(parents=True, exist_ok=True)

    parts = []
    for book, path in ODDS_FILES.items():
        if not path.exists():
            print(f"Skip missing: {path}")
            continue
        parts.append(wide_to_long(pd.read_csv(path), book))

    if not parts:
        raise SystemExit("No Odds/*.csv files found to build offers.")

    offers = pd.concat(parts, ignore_index=True)
    cols = ["sportsbook", "game", "market", "player", "line", "selection", "odds", "odds_format"]
    offers = offers[cols]
    out_path = out_dir / "offers_long.csv"
    offers.to_csv(out_path, index=False)
    print(f"Wrote {out_path} with {len(offers)} rows")


if __name__ == "__main__":
    main()
