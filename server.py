#!/usr/bin/env python3
"""
Secure local drop server for Agent Mode
- POST /save   -> save a file to disk (and optionally mirror into a git repo + commit/push)
- GET  /health -> health check
Security:
- Bearer token auth (DROP_TOKEN env or config)
- Path normalization + allow-list enforcement (glob patterns)
- Optional mirroring into a git repo with branch protections
"""
from flask import Flask, request, jsonify
from pathlib import Path
import os, base64, subprocess

app = Flask(__name__)

# ---- Config (env vars) ----
DROP_TOKEN = os.getenv("DROP_TOKEN", "").strip()
SAVE_BASE_DIR = Path(os.getenv("SAVE_BASE_DIR", "./_agent_out")).resolve()
ALLOW_PATTERNS = [p.strip() for p in os.getenv("ALLOW_PATTERNS", "src/**,tests/**,.ai/**").split(",") if p.strip()]
REPO_DIR = Path(os.getenv("REPO_DIR", "")).resolve() if os.getenv("REPO_DIR") else None
DEFAULT_BRANCH = os.getenv("DEFAULT_BRANCH", "main")
ALLOWED_BRANCH_PREFIXES = [p.strip() for p in os.getenv("ALLOWED_BRANCH_PREFIXES", "lane/,feature/,hotfix/,bugfix/").split(",") if p.strip()]
PROTECTED_BRANCHES = [b.strip() for b in os.getenv("PROTECTED_BRANCHES", "main,master,develop").split(",") if b.strip()]
DISABLE_GIT = os.getenv("DISABLE_GIT", "") == "1"
ALLOW_LOCALHOST_NO_TOKEN = os.getenv("ALLOW_LOCALHOST_NO_TOKEN", "") == "1"

SAVE_BASE_DIR.mkdir(parents=True, exist_ok=True)

def _token_ok():
    if ALLOW_LOCALHOST_NO_TOKEN and request.remote_addr in ("127.0.0.1", "::1"):
        return True
    auth = request.headers.get("Authorization", "")
    return auth.startswith("Bearer ") and DROP_TOKEN and (auth.split(" ",1)[1].strip() == DROP_TOKEN)

def _sanitize_rel_path(rel):
    p = Path(rel)
    if p.is_absolute() or ".." in p.parts:
        return None
    return p

def _match_allowed(rel_path: Path) -> bool:
    from fnmatch import fnmatch
    unix = rel_path.as_posix()
    return any(fnmatch(unix, pat) for pat in ALLOW_PATTERNS)

def _git(*args, cwd=None, check=True):
    return subprocess.run(["git", *args], cwd=cwd, check=check, capture_output=True, text=True)

def _ensure_git_identity(cwd):
    name = os.getenv("GIT_USER_NAME")
    email = os.getenv("GIT_USER_EMAIL")
    if name:  _git("config", "user.name", name, cwd=cwd, check=False)
    if email: _git("config", "user.email", email, cwd=cwd, check=False)

def _ensure_branch(cwd, branch):
    try:
        _git("rev-parse", "--verify", branch, cwd=cwd)
    except subprocess.CalledProcessError:
        _git("fetch", "origin", DEFAULT_BRANCH, cwd=cwd, check=False)
        _git("checkout", "-B", branch, f"origin/{DEFAULT_BRANCH}", cwd=cwd, check=True)
        return
    _git("checkout", branch, cwd=cwd, check=True)

@app.get("/health")
def health():
    return jsonify({
        "ok": True,
        "save_base": str(SAVE_BASE_DIR),
        "repo_dir": str(REPO_DIR) if REPO_DIR else None,
        "allow_patterns": ALLOW_PATTERNS,
        "allowed_branch_prefixes": ALLOWED_BRANCH_PREFIXES,
        "protected_branches": PROTECTED_BRANCHES
    })

@app.post("/save")
def save():
    if not _token_ok():
        return jsonify({"ok": False, "error": "unauthorized"}), 401

    data = request.get_json(silent=True) or {}
    rel = (data.get("path") or "").strip()
    b64 = (data.get("content_b64") or "").strip()
    message = (data.get("message") or "agent: add file").strip()
    branch = (data.get("branch") or "lane/agent-drop").strip()

    rel_path = _sanitize_rel_path(rel)
    if not rel_path:
        return jsonify({"ok": False, "error": "invalid path"}), 400
    if not _match_allowed(rel_path):
        return jsonify({"ok": False, "error": "path not allowed", "allowed": ALLOW_PATTERNS}), 403

    try:
        raw = base64.b64decode(b64.encode("utf-8"), validate=True)
    except Exception:
        return jsonify({"ok": False, "error": "content_b64 invalid"}), 400

    dest = (SAVE_BASE_DIR / rel_path).resolve()
    if SAVE_BASE_DIR not in dest.parents and dest != SAVE_BASE_DIR:
        return jsonify({"ok": False, "error": "path escapes base dir"}), 400
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(raw)

    git_result = None
    if REPO_DIR and not DISABLE_GIT:
        if branch in PROTECTED_BRANCHES:
            return jsonify({"ok": False, "error": f"branch '{branch}' is protected"}), 403
        if not any(branch.startswith(p) for p in ALLOWED_BRANCH_PREFIXES):
            # not fatal, but you can enforce if desired
            pass

        _ensure_git_identity(REPO_DIR)
        _ensure_branch(REPO_DIR, branch)
        repo_target = (REPO_DIR / rel_path)
        repo_target.parent.mkdir(parents=True, exist_ok=True)
        repo_target.write_bytes(raw)

        _git("add", ".", cwd=REPO_DIR, check=True)
        try:
            _git("commit", "-m", message, cwd=REPO_DIR, check=True)
        except subprocess.CalledProcessError:
            git_result = {"commit": "no-op"}
        try:
            _git("push", "origin", branch, cwd=REPO_DIR, check=True)
            git_result = {"push": "ok", "branch": branch}
        except subprocess.CalledProcessError as e:
            git_result = {"push": "failed", "stderr": e.stderr}

    return jsonify({"ok": True, "saved": str(dest), "git": git_result}), 201

if __name__ == "__main__":
    port = int(os.getenv("PORT", "5055"))
    app.run(host="127.0.0.1", port=port)
