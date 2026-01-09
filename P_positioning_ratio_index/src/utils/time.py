# DOC_ID: DOC-LEGACY-0020
import pandas as pd

def robust_resample(df: pd.DataFrame, freq: str, how: str = "last"):
    if df.empty:
        return df
    if how == "last":
        return df.resample(freq).last()
    elif how == "mean":
        return df.resample(freq).mean()
    elif how == "sum":
        return df.resample(freq).sum()
    else:
        raise ValueError("Unsupported resample method")