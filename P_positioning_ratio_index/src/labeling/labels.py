import pandas as pd
import numpy as np

def directional_kbar_label(spot: pd.Series, horizon: int = 5, tp: float = 0.002, sl: float = 0.002):
    fwd = spot.pct_change(horizon).shift(-horizon)
    label = pd.Series(0, index=spot.index)
    label[fwd > tp] = 1
    label[fwd < -sl] = -1
    return label

def triple_barrier_labels(spot: pd.Series, horizon: int = 48, up_mult: float = 2.0, dn_mult: float = 2.0):
    # Simple implementation using rolling window highs/lows as barriers proxy
    ret = spot.pct_change()
    vol = ret.rolling(96).std().shift(1)
    up = spot * (1 + up_mult * vol)
    dn = spot * (1 - dn_mult * vol)
    y = pd.Series(0, index=spot.index)
    for i in range(len(spot)-horizon):
        w = slice(i+1, i+1+horizon)
        if (spot.iloc[w] >= up.iloc[i]).any():
            y.iloc[i] = 1
        elif (spot.iloc[w] <= dn.iloc[i]).any():
            y.iloc[i] = -1
    return y