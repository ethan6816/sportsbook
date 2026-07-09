# sports-ev

Estimate a fair probability from a trusted ("sharp") book — here FanDuel — and
bet against other books (BetMGM, ProphetX) that are mispriced relative to that
estimate. The math is written up in `sports_ev.pdf`; this repo implements it.

## Method (matches `sports_ev.pdf`)

1. **American → decimal** — `d = 1 + 100/|a|` if `a < 0`, else `d = 1 + a/100`.
2. **Implied probability** — `p = 1/d`.
3. **De-vig the sharp book** — proportional method:
   `p_over = p_over_imp / (p_over_imp + p_under_imp)` (and likewise for under),
   so the two sides sum to 1. This is the fair probability `p`.
4. **EV of another book** — `EV = p·(d − 1) − (1 − p)`. Keep bets with `EV` above
   a threshold.
5. **Stake with Kelly** — `f* = (p·b − (1 − p)) / b` where `b = d − 1`; bet a
   quarter of `f*` (fractional Kelly), capped at a fixed fraction of bankroll.

Each step lives in `ev/`: `odds.py` (steps 1–2), `model.py` (steps 3–5),
`normalize.py` (cross-book matching).

## Layout

```
ev/            model package (the math above) + unit tests in tests/
scripts/       build_offers.py, generate_signals.py, run_all_*.py
Crawlers/      per-book link crawlers (FanDuel, BetMGM, ProphetX)
Scrapers/      per-book, per-market odds scrapers -> Odds/*.csv
Links/         event-link CSVs the scrapers read
Odds/          scraped odds, one CSV per book (sample data included)
data/          generated: offers_long.csv, signals.csv
```

## Run the model (no scraping needed — sample `Odds/*.csv` are included)

```bash
pip install -r requirements.txt
python scripts/build_offers.py                 # merge Odds/*.csv -> data/offers_long.csv
python scripts/generate_signals.py --sharp fanduel --bankroll 1000 --min-ev 0.01
python -m pytest tests/                         # verifies the worked example in the PDF
```

`generate_signals.py` writes `data/signals.csv` with the fair probability, the
edge (`ev_per_$`), and the fractional-Kelly `suggested_stake` for each +EV bet.

### Matching across books

Books name the same bet differently (`...-@-...` vs `...-vs-...`; `points ou` vs
`points rebounds assists`; ProphetX appends the stat to player names). The model
normalizes game/market/player to a canonical key; the numeric **line must match
exactly**, since Over 28.5 and Over 27.5 are different bets.

## Refresh the odds yourself (optional, requires live sites)

```bash
playwright install
python scripts/run_all_fanduel.py    # or run_all_betmgm.py / run_all_prophetx.py
python scripts/run_all_books.py      # all three
```

The scrapers drive real sportsbook pages (headful browser, AgentQL, CAPTCHA
handling) and need network access and an AgentQL key; they are the data source,
not part of the tested model path.

> For research/education only. Always check limits, void rules, and line matching
> before placing any bet.
