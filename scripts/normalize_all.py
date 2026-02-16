import os
import pandas as pd
from odds_pipeline.io import load_config, write_csv
from odds_pipeline.normalize import wide_ou_to_long

def main():
    cfg = load_config()
    raw_dir = cfg["paths"]["raw_dir"]
    norm_dir = cfg["paths"]["normalized_dir"]

    # Add more books here as you create raw CSVs
    books = ["fanduel"]  # extend: ["fanduel","draftkings","pinnacle"]

    for book in books:
        raw_path = os.path.join(raw_dir, f"{book}_raw.csv")
        if not os.path.isfile(raw_path):
            print(f"Skip (missing): {raw_path}")
            continue
        df = pd.read_csv(raw_path)
        long_df = wide_ou_to_long(df, sportsbook=book, odds_format="american")
        out_path = os.path.join(norm_dir, f"{book}_long.csv")
        write_csv(long_df, out_path)
        print(f"Wrote {out_path}")

if __name__ == "__main__":
    main()
