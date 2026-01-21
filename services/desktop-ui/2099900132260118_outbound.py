# doc_id: DOC-LEGACY-0070
# DOC_ID: DOC-LEGACY-0006

# bridge/outbound.py (optional illustrative stub)
import json, os, time
from typing import Dict

# Replace this with your socket/named-pipe sender.
# Here we just append JSON lines per-symbol in a folder for illustration.
OUTBOX = os.environ.get("HUEY_OUTBOX", "./outbox")
os.makedirs(OUTBOX, exist_ok=True)

def send_signal_to_mt4(msg: Dict):
    symbol = msg.get("symbol", "UNKNOWN")
    path = os.path.join(OUTBOX, f"{symbol}.jsonl")
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(msg) + "\n")
    return True
