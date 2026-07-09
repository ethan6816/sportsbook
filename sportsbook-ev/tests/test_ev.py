"""Unit tests that pin the model to the worked example in sports_ev.pdf."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ev import (
    american_to_decimal,
    implied_prob,
    devig_proportional,
    fair_prob_from_sharp,
    ev_per_dollar,
    kelly_fraction,
    stake_size,
    normalize_game,
    normalize_market,
    normalize_player,
)

APPROX = 1e-3


def test_american_to_decimal():
    # LaTeX: Dillon Brooks Over 28.5 PRA at -111 -> d = 1.901
    assert abs(american_to_decimal(-111) - 1.9009) < APPROX
    assert abs(american_to_decimal(-115) - 1.8696) < APPROX
    assert abs(american_to_decimal(105) - 2.05) < APPROX
    assert abs(american_to_decimal(100) - 2.0) < APPROX


def test_implied_prob():
    # LaTeX: p_implied = 1/1.901 = 0.526
    assert abs(implied_prob(1.901) - 0.526) < APPROX


def test_devig_matches_latex():
    # Over -111, Under -115 -> fair over prob 0.496
    p_over_imp = implied_prob(american_to_decimal(-111))
    p_under_imp = implied_prob(american_to_decimal(-115))
    p_over, p_under = devig_proportional(p_over_imp, p_under_imp)
    assert abs(p_over - 0.496) < APPROX
    assert abs(p_over + p_under - 1.0) < 1e-9


def test_fair_prob_from_sharp():
    p_over, _ = fair_prob_from_sharp(american_to_decimal(-111), american_to_decimal(-115))
    assert abs(p_over - 0.496) < APPROX


def test_ev_matches_latex():
    # BetMGM +105 (d=2.05) with fair p=0.496 -> EV = 0.017
    assert abs(ev_per_dollar(0.496, 2.05) - 0.017) < APPROX


def test_kelly_matches_latex():
    # f* = 0.016 for p=0.496, d=2.05
    assert abs(kelly_fraction(0.496, 2.05) - 0.016) < APPROX


def test_stake_quarter_kelly_and_cap():
    bankroll = 1000.0
    # quarter Kelly of 0.016 -> ~0.004 of bankroll -> ~$4, under the 2% cap
    assert abs(stake_size(bankroll, 0.496, 2.05, 0.25, 0.02) - 4.0) < 1.0
    # a huge edge should be capped at 2% = $20
    assert stake_size(bankroll, 0.90, 3.0, 0.25, 0.02) == 20.0
    # negative-EV bet -> no stake
    assert stake_size(bankroll, 0.40, 1.5, 0.25, 0.02) == 0.0


def test_normalization_lines_up_books():
    # same game across three books
    fd = normalize_game("phoenix-suns-@-minnesota-timberwolves-35036256")
    bm = normalize_game("phoenix-suns-at-minnesota-timberwolves")
    px = normalize_game("phoenix-suns-vs-minnesota-timberwolves")
    assert fd == bm == px
    # markets
    assert normalize_market("points ou") == "points"
    assert normalize_market("points rebounds assists") == "assists+points+rebounds"
    assert normalize_market("player assists") == "assists"
    # players (prophetx appends the stat word; punctuation/suffixes dropped)
    assert normalize_player("Dillon Brooks Points") == normalize_player("Dillon Brooks")
    assert normalize_player("Royce O'Neale") == "royceoneale"
    assert normalize_player("Trey Murphy III") == "treymurphy"
