#!/usr/bin/env python
import json, time, sys, subprocess
from pathlib import Path
from agentic.config import AgenticConfig
from agentic.router import route_and_generate, run_validators, run_mutators
from agentic.gates import enforce

CFG = AgenticConfig.load()


def audit(event: dict):
    log = Path(CFG.get("paths", "audit_log", default=".ai/.ai-audit.jsonl"))
    log.parent.mkdir(parents=True, exist_ok=True)
    event = {**event, "ts": int(time.time() * 1000)}
    with open(log, "a", encoding="utf-8") as f:
        f.write(json.dumps(event) + "\n")


def preflight_snapshot():
    subprocess.run('git add -A && git commit -m "preflight: snapshot" || true', shell=True)


def main():
    prompt = sys.argv[1] if len(sys.argv) > 1 else "One-line feature description"
    preflight_snapshot()
    audit({"tool": "git", "action": "preflight"})
    manifest, cost = route_and_generate(prompt, CFG)
    Path(".ai").mkdir(exist_ok=True)
    Path(".ai/manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    audit({"tool": "router", "action": "generate", "cost": cost})
    run_validators(CFG)
    audit({"tool": "validators", "action": "validate-ro"})
    run_mutators(CFG)
    audit({"tool": "mutators", "action": "format+fix"})
    subprocess.check_call("pytest --cov=src --cov-fail-under=85 -q", shell=True)
    audit({"tool": "pytest", "action": "coverage>=85"})
    enforce(CFG)
    audit({"tool": "gates", "action": "enforce"})
    print(". Agentic run complete")


if __name__ == "__main__":
    main()

