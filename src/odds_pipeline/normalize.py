from __future__ import annotations
import pandas as pd

def wide_ou_to_long(df: pd.DataFrame, sportsbook: str, odds_format: str = "american") -> pd.DataFrame:
    
    required = {"game","market","player","line","odds_over","odds_under"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing columns in wide OU data: {missing}")

    base_cols = ["game","market","player","line"]
    has_ts = "timestamp_ms" in df.columns

    rows = []
    for _, r in df.iterrows():
        base = {
            "sportsbook": sportsbook,
            "game": r["game"],
            "market": r["market"],
            "player": r["player"],
            "line": r["line"],
            "odds_format": odds_format,
        }
        if has_ts:
            base["timestamp_ms"] = int(r["timestamp_ms"]) if pd.notna(r["timestamp_ms"]) else None

        rows.append({**base, "selection": "OVER", "odds": float(r["odds_over"])})
        rows.append({**base, "selection": "UNDER", "odds": float(r["odds_under"])})

    out = pd.DataFrame(rows)
    return out
