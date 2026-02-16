import os
import csv
from odds_pipeline.io import load_config, ensure_dir

# Example: import your scrapers (adjust paths to your project)
from scrapers.fanduel.assists_ou_fanduel import scrape as scrape_assists
from scrapers.fanduel.rebounds_ou_fanduel import scrape as scrape_rebounds
# from scrapers.fanduel.three_pointers_ou_fanduel import scrape as scrape_threes
# ...

FIELDS = ["game","market","player","line","odds_over","odds_under"]

def append_rows(path: str, rows: list[dict]) -> None:
    file_exists = os.path.isfile(path)
    with open(path, "a", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        if not file_exists:
            w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k) for k in FIELDS})

def main():
    cfg = load_config()
    raw_dir = cfg["paths"]["raw_dir"]
    ensure_dir(raw_dir)

    out_path = os.path.join(raw_dir, "fanduel_raw.csv")

    # IMPORTANT: Each scraper should return list[dict] with keys in FIELDS
    append_rows(out_path, scrape_assists())
    append_rows(out_path, scrape_rebounds())
    # append_rows(out_path, scrape_threes())
    # ...

    print(f"Wrote {out_path}")

if __name__ == "__main__":
    main()
