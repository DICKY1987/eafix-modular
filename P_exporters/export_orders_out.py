#!/usr/bin/env python3
"""
export_orders_out.py

Reads runtime/signals_inbox.csv + registries/matrix_map.csv (+ optional config/parameters.json)
and emits runtime/ea_bridge/orders_out.csv with a computed comment suffix using
`reentry_helpers.hybrid_id`.

Columns emitted (orders_out.csv):
 ts_utc, reentry_key, symbol, side, lot, sl_pips, tp_pips, comment_prefix, comment_suffix, comment

Notes:
 - `comment` is constructed as f"{comment_prefix}_{comment_suffix}" and kept ≤31 chars.
 - Fails closed: any row that cannot be matched/validated is skipped with an error to stderr.
"""

import os, sys, csv, json, datetime
from typing import Dict, Tuple, Optional
from reentry_helpers.hybrid_id import compose as compose_key, validate_key, comment as make_comment, short_hash
from reentry_helpers.vocab import load_vocab

RUNROOT = os.getcwd()  # assume repo root by default

def load_csv(path: str):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))

def load_json(path: str, default=None):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default

def now_utc_iso():
    return datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

def normalize_symbol(sym: str) -> str:
    s = (sym or "").upper()
    # very light normalization; expect 'EURUSD' style
    return s

def matrix_index(rows):
    idx = {}
    for r in rows:
        key = (r["signal_id"], r["time_bucket"], r["outcome_bucket"], r["proximity_bucket"], r["generation"], r.get("direction","ANY"))
        idx[key] = r
    return idx

def main():
    vocab = load_vocab()
    signals_path = os.path.join(RUNROOT, "runtime", "signals_inbox.csv")
    matrix_path  = os.path.join(RUNROOT, "registries", "matrix_map.csv")
    out_dir      = os.path.join(RUNROOT, "runtime", "ea_bridge")
    os.makedirs(out_dir, exist_ok=True)
    out_path     = os.path.join(out_dir, "orders_out.csv")

    params = load_json(os.path.join(RUNROOT, "config", "parameters.json"), default={})
    base_lot = float(params.get("general", {}).get("base_lot", 0.01))
    default_sl = int(params.get("risk", {}).get("sl_pips", 20))
    default_tp = int(params.get("risk", {}).get("tp_pips", 30))
    comment_prefix = params.get("ea", {}).get("comment_prefix", "RNT")

    signals = load_csv(signals_path) if os.path.isfile(signals_path) else []
    matrix  = load_csv(matrix_path) if os.path.isfile(matrix_path) else []
    if not signals:
        print(f"[export_orders_out] No signals found at {signals_path}", file=sys.stderr)
    if not matrix:
        print(f"[export_orders_out] No matrix found at {matrix_path}", file=sys.stderr)

    mindex = matrix_index(matrix)

    with open(out_path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["ts_utc","reentry_key","symbol","side","lot","sl_pips","tp_pips","comment_prefix","comment_suffix","comment"])
        for s in signals:
            symbol = normalize_symbol(s.get("symbol",""))
            sig_id = (s.get("signal_id") or "").upper()
            tb     = (s.get("time_bucket") or s.get("duration") or "").upper()
            ob     = (s.get("outcome_bucket") or s.get("outcome") or "").upper()
            pb     = (s.get("proximity_bucket") or s.get("proximity") or "").upper()
            gen    = int(s.get("generation") or 1)
            side   = (s.get("direction") or "LONG").upper()
            key    = compose_key(sig_id, tb, ob, pb, gen)
            errs   = validate_key(key, vocab)
            if errs:
                print(f"[export_orders_out] skip invalid reentry_key {key}: {errs}", file=sys.stderr)
                continue

            # Match matrix (direction-specific if available, else ANY)
            mx = mindex.get((sig_id,tb,ob,pb,str(gen),side)) or mindex.get((sig_id,tb,ob,pb,str(gen),"ANY"))
            if not mx:
                print(f"[export_orders_out] no matrix row for {key} (side={side})", file=sys.stderr)
                continue

            # Compute params
            risk_mult = float(mx.get("risk_mult") or 1.0)
            sl_mult   = float(mx.get("sl_mult") or 1.0)
            tp_mult   = float(mx.get("tp_mult") or 1.0)
            lot       = round(base_lot * risk_mult, 3)
            sl_pips   = max(1, int(default_sl * sl_mult))
            tp_pips   = max(1, int(default_tp * tp_mult))

            # Comment wiring (prefix + base32 suffix from key)
            suffix = short_hash(key, length=6)
            comment = f"{comment_prefix}_{suffix}"
            # MT4 comment length guard
            if len(comment) > 31:
                comment = comment[:31]

            w.writerow([now_utc_iso(), key, symbol, side, lot, sl_pips, tp_pips, comment_prefix, suffix, comment])

    print(f"[export_orders_out] wrote {out_path}")

if __name__ == "__main__":
    main()
