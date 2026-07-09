
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
    base = Path("Scrapers")
    for sub in ["FanDuel","BetMGM","ProphetX"]:
        code = run_all(base / sub)
        if code != 0:
            raise SystemExit(code)
    raise SystemExit(0)

if __name__ == "__main__":
    main()
