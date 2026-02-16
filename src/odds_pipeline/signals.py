from __future__ import annotations
import pandas as pd
from collections import defaultdict
from .odds import to_decimal, implied_prob_from_decimal, devig_proportional, ev_per_dollar, stake_size

def generate_plus_ev_signals(
    offers: pd.DataFrame,
    sharp_books: set[str],
    bankroll: float,
    min_ev: float,
    kelly_mult: float,
    max_frac_per_bet: float,
) -> pd.DataFrame:
    """
    Expects offers columns:
    sportsbook, game, market, player, line, selection, odds, odds_format, (optional timestamp_ms)

    Works best for 2-way markets (OVER/UNDER). Filters others.
    """
    req = {"sportsbook","game","market","player","line","selection","odds","odds_format"}
    missing = req - set(offers.columns)
    if missing:
        raise ValueError(f"Missing offers columns: {missing}")

    offers = offers.copy()
    offers["odds_decimal"] = offers.apply(lambda r: to_decimal(r["odds"], r["odds_format"]), axis=1)

    group_cols = ["game","market","player","line"]
    signals = []

    for _, g in offers.groupby(group_cols):
        selections = sorted(g["selection"].unique())
        if len(selections) != 2:
            continue

        sharp = g[g["sportsbook"].isin(sharp_books)]
        soft  = g[~g["sportsbook"].isin(sharp_books)]
        if sharp.empty or soft.empty:
            continue

        # best sharp per selection
        best_sharp = sharp.sort_values("odds_decimal", ascending=False).groupby("selection").head(1)
        if set(best_sharp["selection"]) != set(selections):
            continue

        # fair probs via de-vig
        implied = []
        for s in selections:
            d = float(best_sharp[best_sharp["selection"] == s]["odds_decimal"].iloc[0])
            implied.append(implied_prob_from_decimal(d))
        fair = devig_proportional(implied)
        p_true = {selections[i]: fair[i] for i in range(2)}

        # best soft per selection
        best_soft = soft.sort_values("odds_decimal", ascending=False).groupby("selection").head(1)

        for s in selections:
            row = best_soft[best_soft["selection"] == s]
            if row.empty:
                continue
            row = row.iloc[0]
            d = float(row["odds_decimal"])
            ev = ev_per_dollar(float(p_true[s]), d)
            if ev >= min_ev:
                amt = stake_size(bankroll, float(p_true[s]), d, kelly_mult, max_frac_per_bet)
                if amt > 0:
                    signals.append({
                        "sportsbook": row["sportsbook"],
                        "game": row["game"],
                        "market": row["market"],
                        "player": row["player"],
                        "line": row["line"],
                        "selection": s,
                        "odds_decimal": d,
                        "p_true": float(p_true[s]),
                        "ev_per_$": float(ev),
                        "suggested_stake": float(amt),
                    })

    out = pd.DataFrame(signals)
    if len(out):
        out = out.sort_values("ev_per_$", ascending=False)
    return out
