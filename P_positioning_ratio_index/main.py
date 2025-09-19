import os
import pandas as pd
import numpy as np
from pathlib import Path
from src.utils.io import ensure_dirs, load_config, save_parquet
from src.data_sources.cftc_cot import get_cot_disaggregated
from src.data_sources.oanda_sentiment import get_oanda_sentiment_series
from src.data_sources.ig_sentiment import get_ig_sentiment
from src.features.positioning import make_institutional_features, make_retail_features, combine_inst_retail, shift_features
import matplotlib.pyplot as plt

def plot_series(df: pd.DataFrame, cols, out_path: str, title: str):
    plt.figure(figsize=(12,5))
    df[cols].dropna().plot()
    plt.title(title)
    plt.tight_layout()
    Path(os.path.dirname(out_path)).mkdir(parents=True, exist_ok=True)
    plt.savefig(out_path, dpi=150)
    plt.close()

def run(cfg_path="config.yaml"):
    cfg = load_config(cfg_path)
    sym_list = cfg["general"]["symbols"]
    bar = cfg["general"]["bar"]
    out_dir = cfg["general"]["out_dir"]
    plot_dir = cfg["general"]["plot_dir"]

    ensure_dirs("data/raw", out_dir, plot_dir, "artifacts", "artifacts/plots")

    # 1) Institutional (COT)
    if cfg["cftc"]["enabled"]:
        print("Downloading CFTC COT (disaggregated)...")
        cot = get_cot_disaggregated()
    else:
        cot = pd.DataFrame(columns=["report_date","pair","inst_net_ratio"])

    inst = make_institutional_features(cot, bar)

    # 2) Retail (OANDA / IG / both)
    all_features = []
    for pair in sym_list:
        per_pair = pd.DataFrame(index=inst.index if not inst.empty else None)

        # OANDA retail
        if cfg["oanda"]["enabled"]:
            instrument = cfg["oanda"]["instruments_map"].get(pair, None)
            tok = cfg["oanda"]["token"]
            if instrument and tok and tok != "REPLACE_WITH_OANDA_V20_TOKEN":
                print(f"Fetching OANDA sentiment for {instrument} ...")
                retail_oanda = get_oanda_sentiment_series(instrument, tok, n_samples=1, sleep_sec=1, account_type=cfg["oanda"]["account_type"])
                r_o = make_retail_features(retail_oanda, pair, bar)
                per_pair = r_o if per_pair.empty else per_pair.join(r_o, how="outer")

        # IG / DailyFX
        if cfg["ig"]["enabled"] or cfg["ig"]["use_dailyfx_public"]:
            try:
                retail_ig = get_ig_sentiment(cfg["ig"]["use_dailyfx_public"], cfg["ig"]["api_key"], cfg["ig"]["identifier"], cfg["ig"]["password"])
                # If implemented to return pct_long/short, add here
            except Exception:
                pass

        # Combine with institutional & build divergence
        combined = combine_inst_retail(inst, per_pair, pair) if not inst.empty else per_pair
        combined = shift_features(combined, 1)
        all_features.append(combined)

        if not combined.empty:
            cols_to_plot = [c for c in combined.columns if c.endswith(("_inst_net_ratio_z", "_retail_ls_ratio_z", "_positioning_divergence")) and pair in c]
            if cols_to_plot:
                plot_series(combined, cols_to_plot, f"{plot_dir}/positioning_index_{pair}.png", f"Positioning Index – {pair}")

    if all_features:
        feat = pd.concat(all_features, axis=1).sort_index()
    else:
        feat = inst

    save_parquet(feat, f"{out_dir}/features.parquet")
    print(f"Saved features to {out_dir}/features.parquet")

if __name__ == "__main__":
    run()