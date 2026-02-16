import os
from odds_pipeline.io import load_config, write_csv
from odds_pipeline.merge import merge_csvs

def main():
    cfg = load_config()
    norm_dir = cfg["paths"]["normalized_dir"]
    merged_dir = cfg["paths"]["merged_dir"]

    books = cfg["books"]["active_books"]
    paths = [os.path.join(norm_dir, f"{b}_long.csv") for b in books if os.path.isfile(os.path.join(norm_dir, f"{b}_long.csv"))]

    merged = merge_csvs(paths)
    out_path = os.path.join(merged_dir, "offers.csv")
    write_csv(merged, out_path)
    print(f"Wrote {out_path} with {len(merged)} rows")

if __name__ == "__main__":
    main()
