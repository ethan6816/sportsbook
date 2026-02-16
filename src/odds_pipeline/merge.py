from __future__ import annotations
import pandas as pd

def merge_csvs(paths: list[str]) -> pd.DataFrame:
    dfs = [pd.read_csv(p) for p in paths]
    return pd.concat(dfs, ignore_index=True) if dfs else pd.DataFrame()
