# This is a Sports Odds Pipeline 

A modular sports odds data pipeline for:
- scraping sportsbook odds (per market/stat)
- normalizing disparate formats into a unified schema
- merging multiple books into a single offers feed
- generating betting signals (+EV vs a sharp reference; arb checks optional)

## Quickstart
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cp config/config.example.yaml config/config.yaml
make run
