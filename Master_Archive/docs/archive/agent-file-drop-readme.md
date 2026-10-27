# Agent File Drop + Actions Bundle

## 1) Local drop server
- Location: `agent_file_drop/server.py`
- Install deps: `pip install -r agent_file_drop/requirements.txt`
- Configure env: see `agent_file_drop/env.example`
- Run: `python agent_file_drop/server.py` (default port 5055)

Secure by:
- Bearer token (DROP_TOKEN)
- Allowed path globs (ALLOW_PATTERNS)
- Optional mirroring to a local repo + auto-commit/push
- Protected branches blocked; lane prefixes encouraged

## 2) OpenAPI GPT Actions
- Local drop action: `.ai/actions/openapi_local_drop.yaml` (set your tunnel URL; pass Bearer DROP_TOKEN)
- GitHub writer action: `.ai/actions/openapi_github_file_writer.yaml` (attach GitHub PAT with repo:contents)

Import these into ChatGPT "Actions" (custom GPT) and provide the appropriate auth.

## 3) VS Code extension snippets
- `vscode_extension_snippets/githubSave.ts` — save to GitHub via Octokit.
- `vscode_extension_snippets/config.schema.json` — JSON schema for your config webview.

## Tips
- Expose the local server securely via Cloudflare Tunnel or equivalent, and use a strong DROP_TOKEN.
- The server only writes files matching `src/**`, `tests/**`, `.ai/**` by default (change with ALLOW_PATTERNS).
- To auto-commit/push, set REPO_DIR to a local clone that has credentials set for origin push.
