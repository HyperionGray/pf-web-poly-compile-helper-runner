#!/usr/bin/env python3
"""
Standardize GitHub labels across repositories.

This script ensures a consistent set of labels exist (and optionally updates
their color/description) across many repositories.

Examples:
  # Dry-run across default owners (ALL)
  python standardize_labels.py --target ALL --dry-run

  # Apply across all repos in default owners
  export GITHUB_TOKEN="..."
  python standardize_labels.py --target ALL --update-existing

  # Apply to a single org
  python standardize_labels.py --target P4X-ng/*

  # Apply to a single repo
  python standardize_labels.py --target P4X-ng/some-repo
"""

from __future__ import annotations

import argparse
import os
import sys
import time
from typing import Any, Dict, Iterable, List, Optional, Tuple

import requests


DEFAULT_OWNERS = ["P4X-ng", "HyperionGray", "TeamHG-Memex", "hyp3ri0n-ng"]


LabelSpec = Dict[str, str]


DEFAULT_LABELS: List[LabelSpec] = [
    {
        "name": "automation",
        "color": "5319E7",
        "description": "Automation-generated direction and planning",
    },
    {
        "name": "ai-review",
        "color": "0E8A16",
        "description": "Trigger LLM PR review (default provider/model)",
    },
    # OpenAI (label name is also the model string for workflows)
    {"name": "gpt-5.2", "color": "1D76DB", "description": "Trigger LLM review (OpenAI)"},
    {"name": "gpt-5.2-pro", "color": "1D76DB", "description": "Trigger LLM review (OpenAI)"},
    {"name": "gpt-5.1", "color": "1D76DB", "description": "Trigger LLM review (OpenAI)"},
    {"name": "gpt-5.1-codex", "color": "1D76DB", "description": "Trigger LLM review (OpenAI)"},
    # Gemini (label name is also the model string for workflows)
    {"name": "gemini3", "color": "C2E0C6", "description": "Trigger LLM review (Gemini)"},
    {"name": "gemini-3", "color": "C2E0C6", "description": "Trigger LLM review (Gemini)"},
    # Anthropic / Claude
    {"name": "claude-4.5-opus", "color": "D93F0B", "description": "Trigger LLM review (Anthropic)"},
    {"name": "claude-4.5-thinking", "color": "D93F0B", "description": "Trigger LLM review (Anthropic)"},
    # Copilot assignment / normalization labels (kept for back-compat)
    {"name": "copilot", "color": "0E8A16", "description": "Assign this issue to GitHub Copilot"},
    {"name": "copilot-gpt-5.1", "color": "5319E7", "description": "Legacy Copilot model selection label"},
    {"name": "copilot-gpt-5.1-codex", "color": "1D76DB", "description": "Legacy Copilot model selection label"},
    {"name": "copilot-claude-4.5-opus", "color": "D93F0B", "description": "Legacy Copilot model selection label"},
    {"name": "copilot-model:gpt-5.2", "color": "BFDADC", "description": "Preferred Copilot model selection label"},
    {"name": "copilot-model:gpt-5.2-pro", "color": "BFDADC", "description": "Preferred Copilot model selection label"},
    {"name": "copilot-model:gpt-5.1", "color": "BFDADC", "description": "Preferred Copilot model selection label"},
    {"name": "copilot-model:gpt-5.1-codex", "color": "BFDADC", "description": "Preferred Copilot model selection label"},
]


def gh_headers(token: str) -> Dict[str, str]:
    return {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }


def get_all_repos(owner: str, token: str, include_archived: bool) -> List[Dict[str, Any]]:
    headers = gh_headers(token)
    repos: List[Dict[str, Any]] = []
    page = 1
    per_page = 100

    while True:
        url = f"https://api.github.com/orgs/{owner}/repos"
        params = {"per_page": per_page, "page": page, "type": "all"}
        resp = requests.get(url, headers=headers, params=params, timeout=60)
        if resp.status_code == 404:
            url = f"https://api.github.com/users/{owner}/repos"
            resp = requests.get(url, headers=headers, params=params, timeout=60)

        if resp.status_code != 200:
            print(f"Error fetching repositories for {owner}: {resp.status_code}")
            try:
                print(resp.text)
            except Exception:
                pass
            return []

        batch = resp.json()
        if not batch:
            break
        repos.extend(batch)
        if len(batch) < per_page:
            break
        page += 1

    if not include_archived:
        repos = [r for r in repos if not r.get("archived", False)]

    return repos


def list_labels(owner: str, repo: str, token: str) -> List[Dict[str, Any]]:
    headers = gh_headers(token)
    labels: List[Dict[str, Any]] = []
    page = 1
    per_page = 100

    while True:
        url = f"https://api.github.com/repos/{owner}/{repo}/labels"
        resp = requests.get(url, headers=headers, params={"per_page": per_page, "page": page}, timeout=60)
        if resp.status_code != 200:
            return []

        batch = resp.json()
        if not batch:
            break
        labels.extend(batch)
        if len(batch) < per_page:
            break
        page += 1

    return labels


def create_label(owner: str, repo: str, token: str, spec: LabelSpec) -> Tuple[bool, str]:
    headers = gh_headers(token)
    url = f"https://api.github.com/repos/{owner}/{repo}/labels"
    payload = {"name": spec["name"], "color": spec["color"], "description": spec.get("description", "")}
    resp = requests.post(url, headers=headers, json=payload, timeout=60)
    if resp.status_code in (201,):
        return True, "created"
    if resp.status_code == 422:
        return False, "already exists or invalid"
    return False, f"create failed: {resp.status_code}"


def update_label(owner: str, repo: str, token: str, name: str, spec: LabelSpec) -> Tuple[bool, str]:
    headers = gh_headers(token)
    url = f"https://api.github.com/repos/{owner}/{repo}/labels/{name}"
    payload = {"color": spec["color"], "description": spec.get("description", "")}
    resp = requests.patch(url, headers=headers, json=payload, timeout=60)
    if resp.status_code == 200:
        return True, "updated"
    if resp.status_code == 404:
        return False, "not found"
    return False, f"update failed: {resp.status_code}"


def normalize_label_name(name: str) -> str:
    return name.strip()


def ensure_labels_for_repo(
    owner: str,
    repo: str,
    token: str,
    label_specs: Iterable[LabelSpec],
    update_existing: bool,
    dry_run: bool,
    delay_s: float,
) -> Tuple[int, int, int]:
    existing = list_labels(owner, repo, token)
    existing_by_name = {normalize_label_name(l.get("name", "")): l for l in existing if isinstance(l, dict)}

    created = 0
    updated = 0
    skipped = 0

    for spec in label_specs:
        name = normalize_label_name(spec["name"])
        if not name:
            continue

        cur = existing_by_name.get(name)
        if not cur:
            if dry_run:
                print(f"  create label: {name}")
                skipped += 1
            else:
                ok, msg = create_label(owner, repo, token, spec)
                if ok:
                    created += 1
                else:
                    print(f"  label create failed: {name} ({msg})")
            time.sleep(delay_s)
            continue

        if not update_existing:
            skipped += 1
            continue

        desired_color = spec.get("color", "").lower()
        desired_desc = spec.get("description", "")
        cur_color = str(cur.get("color", "")).lower()
        cur_desc = str(cur.get("description", "") or "")

        if cur_color == desired_color and cur_desc == desired_desc:
            skipped += 1
            continue

        if dry_run:
            print(f"  update label: {name}")
            skipped += 1
        else:
            ok, msg = update_label(owner, repo, token, name, spec)
            if ok:
                updated += 1
            else:
                print(f"  label update failed: {name} ({msg})")
        time.sleep(delay_s)

    return created, updated, skipped


def parse_target(target: str) -> Tuple[str, Optional[str]]:
    if target in ("ALL", "*", "all"):
        return "ALL", None
    if target.endswith("/*"):
        return target.split("/", 1)[0], "*"
    if "/" in target:
        owner, repo = target.split("/", 1)
        return owner, repo
    raise ValueError("Target must be 'ALL', 'Owner/*', or 'Owner/Repo'")


def main() -> int:
    parser = argparse.ArgumentParser(description="Standardize GitHub labels across repositories")
    parser.add_argument("--target", default="ALL", help='Target: "Owner/Repo", "Owner/*", or "ALL"')
    parser.add_argument("--owners", default="", help="Comma-separated owners to scan when target is ALL")
    parser.add_argument("--include-archived", action="store_true", help="Include archived repositories")
    parser.add_argument("--token", help="GitHub token (or set GITHUB_TOKEN env var)")
    parser.add_argument("--dry-run", action="store_true", help="Show planned changes without applying")
    parser.add_argument("--update-existing", action="store_true", help="Update color/description for existing labels")
    parser.add_argument("--delay", type=float, default=0.2, help="Delay between API calls (seconds)")

    args = parser.parse_args()

    token = args.token or os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if not token:
        print("Error: GitHub token required (GITHUB_TOKEN env var or --token)")
        return 2

    try:
        owner, repo_sel = parse_target(args.target)
    except ValueError as e:
        print(f"Error: {e}")
        return 2

    owners: List[str]
    if owner == "ALL":
        if args.owners.strip():
            owners = [o.strip() for o in args.owners.split(",") if o.strip()]
        else:
            owners = DEFAULT_OWNERS
    else:
        owners = [owner]

    repos: List[Tuple[str, str]] = []
    if owner == "ALL" or repo_sel == "*":
        for o in owners:
            print(f"Fetching repositories for {o}...")
            for r in get_all_repos(o, token, include_archived=args.include_archived):
                repos.append((o, r.get("name", "")))
    else:
        repos = [(owner, repo_sel or "")]

    repos = [(o, r) for (o, r) in repos if r]
    print(f"Repositories to process: {len(repos)}")

    total_created = 0
    total_updated = 0
    total_skipped = 0
    total_failed = 0

    for o, r in repos:
        full = f"{o}/{r}"
        print(full)
        try:
            created, updated, skipped = ensure_labels_for_repo(
                o,
                r,
                token,
                DEFAULT_LABELS,
                update_existing=args.update_existing,
                dry_run=args.dry_run,
                delay_s=max(args.delay, 0.0),
            )
            total_created += created
            total_updated += updated
            total_skipped += skipped
        except Exception as e:
            total_failed += 1
            print(f"  unexpected error: {e}")

    print("Summary")
    print(f"  Labels created: {total_created}")
    print(f"  Labels updated: {total_updated}")
    print(f"  Labels skipped: {total_skipped}")
    print(f"  Repos failed:   {total_failed}")

    return 0 if total_failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
