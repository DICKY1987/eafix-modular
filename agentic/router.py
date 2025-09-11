import subprocess
from .config import AgenticConfig
from .retry import with_retry


def usd_estimate_from_tokens(i, o, model="claude-opus"):
    return (i + o) * 0.000015


def _run(cmd):
    p = subprocess.run(cmd, shell=True)
    if p.returncode != 0:
        raise RuntimeError(f"Command failed: {cmd}")


def generator_llm(prompt: str) -> dict:
    return {"plan": prompt, "changed_files": [], "followups": []}


def generator_oss(prompt: str) -> dict:
    return {"plan": prompt, "changed_files": [], "followups": ["manual refinement or aider"]}


def _should_use_llm(cfg: AgenticConfig, impact: float, toks: int) -> bool:
    if impact < cfg.get("routing", "min_confidence_for_llm", default=0.6):
        return False
    return usd_estimate_from_tokens(toks // 2, toks // 2) <= cfg.get("cost", "hard_cap_usd_per_task", default=5.0)


def route_and_generate(prompt: str, cfg: AgenticConfig, impact_score=0.7, estimated_tokens=8000):
    use_llm = ("claude" in (cfg.get("routing", "provider_priority", default=["oss"]) or [])) and _should_use_llm(
        cfg, impact_score, estimated_tokens
    )
    gen = (lambda: generator_llm(prompt)) if use_llm else (lambda: generator_oss(prompt))
    manifest = with_retry(
        gen,
        attempts=cfg.get("retries", "attempts", default=2),
        backoff=tuple(cfg.get("retries", "backoff_seconds", default=[2, 5])),
    )
    cost = usd_estimate_from_tokens(estimated_tokens // 2, estimated_tokens // 2) if use_llm else 0.0
    return manifest, {"provider": "claude" if use_llm else "oss", "estimated_cost_usd": cost}


def run_validators(cfg: AgenticConfig):
    for cmd in (cfg.get("validators", "read_only_parallel", default=[]) or []):
        _run(cmd)


def run_mutators(cfg: AgenticConfig):
    for cmd in (cfg.get("mutators_serial", default=[]) or []):
        _run(cmd)

