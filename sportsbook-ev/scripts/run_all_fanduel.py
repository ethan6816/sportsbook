
from __future__ import annotations
import os, sys, subprocess
from pathlib import Path

def run_all(folder: Path) -> int:
    py = sys.executable
    files = sorted([p for p in folder.glob("*.py") if p.name != "__init__.py"])
    if not files:
        print(f"No scraper files found in {folder}")
        return 1
    print(f"Running {len(files)} scrapers in {folder}...")
    for p in files:
        print(f"\n=== {p.name} ===")
        r = subprocess.run([py, str(p)], cwd=str(folder.parent.parent), check=False)
        if r.returncode != 0:
            print(f"Scraper failed: {p.name} (exit {r.returncode})")
            return r.returncode
    print("\nDone.")
    return 0

def main():
    folder = Path("Scrapers") / "FanDuel"
    raise SystemExit(run_all(folder))

if __name__ == "__main__":
    main()
