# DOC_ID: DOC-LEGACY-0019
import os
import pandas as pd
from pathlib import Path

def ensure_dirs(*paths):
    for p in paths:
        Path(p).mkdir(parents=True, exist_ok=True)

def save_parquet(df: pd.DataFrame, path: str):
    Path(os.path.dirname(path)).mkdir(parents=True, exist_ok=True)
    df.to_parquet(path, index=True)

def save_csv(df: pd.DataFrame, path: str):
    Path(os.path.dirname(path)).mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=True)

def load_config(path: str):
    import yaml
    with open(path, "r") as f:
        return yaml.safe_load(f)