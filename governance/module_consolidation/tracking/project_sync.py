#!/usr/bin/env python3
"""
Project the consolidation SSOT onto GitHub Issues + a Projects v2 board.

Direction is ONE-WAY: repo -> GitHub.

The plan (Section 3) classifies catalogs, summaries and projections as *derived*
views that must never be edited as independent specifications. A GitHub Project
is exactly such a view, so this tool:

  * writes issue/field state FROM the SSOT,
  * never reads GitHub state back into the SSOT,
  * reports drift when someone edits a projected field in the UI.

Idempotency key: an HTML marker '<!-- ssot-id: X -->' embedded in each issue body.

Requires: gh CLI authenticated with the 'project' scope.
  gh auth refresh -s project -s read:project
"""
from __future__ import annotations
import argparse, json, subprocess, sys, textwrap

MARKER = "<!-- ssot-id: {} -->"


def gh(args, inp=None):
    r = subprocess.run(["gh", *args], capture_output=True, text=True, input=inp)
    if r.returncode != 0:
        raise RuntimeError(f"gh {' '.join(args)} failed:\n{r.stderr.strip()}")
    return r.stdout


def graphql(query, **variables):
    args = ["api", "graphql", "-f", f"query={query}"]
    for k, v in variables.items():
        args += ["-f" if isinstance(v, str) else "-F", f"{k}={v}"]
    return json.loads(gh(args))


# ---------------------------------------------------------------- discovery
def project_meta(owner, number):
    q = """
    query($owner:String!, $number:Int!){
      user(login:$owner){ projectV2(number:$number){ id title
        fields(first:50){ nodes{
          ... on ProjectV2FieldCommon { id name dataType }
          ... on ProjectV2SingleSelectField { id name options { id name } } } } } }
      organization(login:$owner){ projectV2(number:$number){ id title
        fields(first:50){ nodes{
          ... on ProjectV2FieldCommon { id name dataType }
          ... on ProjectV2SingleSelectField { id name options { id name } } } } } }
    }"""
    try:
        d = graphql(q, owner=owner, number=int(number))["data"]
    except RuntimeError as e:
        d = None
        for scope in ("user", "organization"):
            sub = f"""query($owner:String!,$number:Int!){{ {scope}(login:$owner){{
              projectV2(number:$number){{ id title fields(first:50){{ nodes{{
              ... on ProjectV2FieldCommon {{ id name dataType }}
              ... on ProjectV2SingleSelectField {{ id name options {{ id name }} }} }} }} }} }} }}"""
            try:
                d = graphql(sub, owner=owner, number=int(number))["data"]
                break
            except RuntimeError:
                continue
        if d is None:
            raise e
    node = (d.get("user") or d.get("organization") or {}).get("projectV2")
    if not node:
        raise SystemExit(f"Project #{number} not found for owner {owner}.")
    fields = {}
    for f in node["fields"]["nodes"]:
        if not f:
            continue
        fields[f["name"]] = {
            "id": f["id"],
            "options": {o["name"]: o["id"] for o in f.get("options", [])},
        }
    return node["id"], node["title"], fields


def existing_issues(repo, label="consolidation"):
    """Map ssot_id -> issue dict, using the body marker as the key."""
    out = gh(["issue", "list", "--repo", repo, "--label", label, "--state", "all",
              "--limit", "500", "--json", "number,title,body,id,state"])
    found = {}
    for it in json.loads(out):
        body = it.get("body") or ""
        for line in body.splitlines():
            line = line.strip()
            if line.startswith("<!-- ssot-id:") and line.endswith("-->"):
                found[line[len("<!-- ssot-id:"):-3].strip()] = it
                break
    return found


# ------------------------------------------------------------------ writing
def ensure_labels(repo, labels):
    have = {l["name"] for l in json.loads(
        gh(["label", "list", "--repo", repo, "--limit", "200", "--json", "name"]))}
    colors = {"consolidation": "0E8A16", "phase": "1D76DB", "gate": "B60205",
              "decision": "D93F0B", "deliverable": "5319E7", "wave": "FBCA04",
              "module": "C2E0C6", "pilot": "E99695", "blocking": "B60205"}
    for l in sorted(labels - have):
        try:
            gh(["label", "create", l, "--repo", repo, "--color", colors.get(l, "EDEDED"),
                "--description", "EAFIX consolidation tracking"])
            print(f"  + label {l}")
        except RuntimeError:
            pass


def body_with_marker(item):
    return f"{item['body']}\n\n{MARKER.format(item['ssot_id'])}\n"


def create_issue(repo, item):
    args = ["issue", "create", "--repo", repo, "--title", item["title"],
            "--body", body_with_marker(item)]
    for l in item.get("labels", []):
        args += ["--label", l]
    url = gh(args).strip().splitlines()[-1]
    return url


def update_issue_body(repo, number, item):
    gh(["issue", "edit", str(number), "--repo", repo, "--body", body_with_marker(item)])


def issue_node_id(repo, number):
    owner, name = repo.split("/")
    q = """query($owner:String!,$name:String!,$number:Int!){
      repository(owner:$owner,name:$name){ issue(number:$number){ id } } }"""
    return graphql(q, owner=owner, name=name, number=int(number))["data"]["repository"]["issue"]["id"]


def add_sub_issue(parent_id, child_id):
    m = """mutation($p:ID!,$c:ID!){ addSubIssue(input:{issueId:$p, subIssueId:$c}){
             issue { number } subIssue { number } } }"""
    try:
        graphql(m, p=parent_id, c=child_id)
        return True
    except RuntimeError as e:
        msg = str(e).lower()
        if "already" in msg or "duplicate" in msg or "one parent" in msg:
            return False
        raise


def add_to_project(project_id, content_id):
    m = """mutation($p:ID!,$c:ID!){ addProjectV2ItemById(input:{projectId:$p, contentId:$c}){
             item { id } } }"""
    return graphql(m, p=project_id, c=content_id)["data"]["addProjectV2ItemById"]["item"]["id"]


def set_field(project_id, item_id, field, value):
    """field = {'id':..., 'options': {...}}; value = str"""
    if field["options"]:
        opt = field["options"].get(value)
        if opt is None:
            return f"option '{value}' not defined"
        val = f'{{singleSelectOptionId: "{opt}"}}'
    else:
        val = f'{{text: {json.dumps(value)}}}'
    m = f"""mutation{{ updateProjectV2ItemFieldValue(input:{{
             projectId:"{project_id}", itemId:"{item_id}",
             fieldId:"{field['id']}", value:{val} }}){{ projectV2Item{{ id }} }} }}"""
    graphql(m)
    return None


# --------------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--owner", required=True, help="project owner (user or org)")
    ap.add_argument("--project", required=True, help="project number")
    ap.add_argument("--repo", required=True, help="owner/name for the issues")
    ap.add_argument("--ssot", default="eafix_consolidation_ssot.json")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--only", help="comma-separated item types (Phase,Gate,Decision,Deliverable,Wave,Module)")
    a = ap.parse_args()

    ssot = json.load(open(a.ssot))
    items = ssot["items"]
    if a.only:
        keep = {s.strip() for s in a.only.split(",")}
        items = [i for i in items if i["item_type"] in keep]

    print(f"SSOT {a.ssot}  v{ssot['ssot_version']}  baseline {ssot['baseline_commit'][:12]}")
    print(f"{len(items)} items to project\n")

    if a.dry_run:
        by = {}
        for i in items:
            by.setdefault(i["item_type"], []).append(i)
        for t in ("Phase", "Gate", "Decision", "Deliverable", "Wave", "Module"):
            if t in by:
                print(f"{t} ({len(by[t])})")
                for i in by[t][:4]:
                    print(f"   {i['ssot_id']:14s} {i['title']}")
                if len(by[t]) > 4:
                    print(f"   ... {len(by[t])-4} more")
        print("\nNot tracked in GitHub (owned by the repo ledger):")
        for n in ssot["not_tracked_in_github"]:
            print(f"   - {n}")
        print("\nDry run only. No changes made.")
        return

    project_id, title, fields = project_meta(a.owner, a.project)
    print(f"Project: {title} ({project_id})")
    missing = [f for f in ("Item Type", "Phase", "Wave", "SSOT ID") if f not in fields]
    if missing:
        raise SystemExit(f"Missing fields {missing}. Run project_bootstrap.py first.")

    ensure_labels(a.repo, {l for i in items for l in i.get("labels", [])})
    existing = existing_issues(a.repo)
    print(f"Found {len(existing)} already-projected issues\n")

    node_ids, drift, created, updated = {}, [], 0, 0

    # pass 1 — issues
    for it in items:
        sid = it["ssot_id"]
        if sid in existing:
            cur = existing[sid]
            if (cur.get("body") or "").strip() != body_with_marker(it).strip():
                update_issue_body(a.repo, cur["number"], it)
                drift.append(f"{sid}: issue body differed from SSOT; overwritten from repo")
                updated += 1
            node_ids[sid] = cur["id"]
            num = cur["number"]
        else:
            url = create_issue(a.repo, it)
            num = int(url.rstrip("/").split("/")[-1])
            node_ids[sid] = issue_node_id(a.repo, num)
            created += 1
            print(f"  + #{num:<5} {it['title']}")
        it["_number"] = num

    # pass 2 — sub-issue hierarchy (max 100 children, 8 levels; we use 3)
    for it in items:
        p = it.get("parent")
        if p and p in node_ids and it["ssot_id"] in node_ids:
            try:
                add_sub_issue(node_ids[p], node_ids[it["ssot_id"]])
            except RuntimeError as e:
                drift.append(f"{it['ssot_id']}: sub-issue link failed — {e}")

    # pass 3 — project items + fields
    for it in items:
        sid = it["ssot_id"]
        try:
            item_id = add_to_project(project_id, node_ids[sid])
        except RuntimeError as e:
            drift.append(f"{sid}: add to project failed — {e}")
            continue
        vals = dict(it["fields"])
        vals["SSOT ID"] = sid
        for fname, fval in vals.items():
            if fname not in fields:
                drift.append(f"{sid}: field '{fname}' not on project")
                continue
            err = set_field(project_id, item_id, fields[fname], str(fval))
            if err:
                drift.append(f"{sid}: {fname} — {err}")

    print(f"\ncreated {created}   body-corrected {updated}")
    if drift:
        print(f"\nDRIFT / WARNINGS ({len(drift)}):")
        for d in drift:
            print(f"  ! {d}")
        print("\nProjected fields are derived. Edit the SSOT and re-run; do not fix them in the UI.")
    else:
        print("\nNo drift. Projection matches the SSOT.")


if __name__ == "__main__":
    try:
        main()
    except RuntimeError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)
