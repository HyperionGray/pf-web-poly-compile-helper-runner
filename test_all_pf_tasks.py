#!/usr/bin/env python3
"""
Comprehensive pf task validation (safe, no task execution).

Validates:
  - Runner is available (defaults to `python3 pf-runner/pf_main.py`, or `pf` with --use-system-pf)
  - `pf prune` passes (syntax validation)
  - `pf list` returns tasks, all with descriptions, and aliases are unique
  - `pf help <task>` works for every task (parseability)
"""

from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple


@dataclass(frozen=True)
class TaskInfo:
    name: str
    description: str
    aliases: Tuple[str, ...]


def _repo_root() -> Path:
    return Path(__file__).resolve().parent


def _pf_cmd(repo_root: Path, use_system_pf: bool) -> List[str]:
    repo_runner = repo_root / "pf-runner" / "pf_main.py"

    if not use_system_pf and repo_runner.exists():
        return ["python3", str(repo_runner)]

    if shutil.which("pf"):
        return ["pf"]

    if repo_runner.exists():
        return ["python3", str(repo_runner)]

    raise FileNotFoundError("Neither `pf` nor `pf-runner/pf_main.py` found")


def _run(
    args: Sequence[str],
    repo_root: Path,
    timeout_s: int,
    capture_output: bool = True,
) -> subprocess.CompletedProcess:
    return subprocess.run(
        list(args),
        cwd=str(repo_root),
        text=True,
        capture_output=capture_output,
        timeout=timeout_s,
    )


_TASK_LINE_RE = re.compile(r"^\s{2}([A-Za-z0-9][A-Za-z0-9_-]*)\b")
_ALIASES_RE = re.compile(r"\(aliases:\s*([^)]+)\)\s*$")


def _parse_pf_list(output: str) -> List[TaskInfo]:
    tasks: List[TaskInfo] = []
    for raw in output.splitlines():
        line = raw.rstrip("\n")
        m = _TASK_LINE_RE.match(line)
        if not m:
            continue

        name = m.group(1)
        remainder = line[m.end() :].strip()

        description = ""
        aliases: Tuple[str, ...] = ()

        if remainder.startswith("-"):
            remainder = remainder[1:].lstrip()
            alias_match = _ALIASES_RE.search(remainder)
            if alias_match:
                alias_str = alias_match.group(1)
                aliases = tuple(a.strip() for a in alias_str.split(",") if a.strip())
                description = remainder[: alias_match.start()].rstrip()
            else:
                description = remainder.strip()
        else:
            # No description printed for this task.
            description = ""

        tasks.append(TaskInfo(name=name, description=description, aliases=aliases))

    # Deduplicate while preserving order (in case `pf list` repeats tasks in multiple groups).
    seen: set[str] = set()
    unique: List[TaskInfo] = []
    for t in tasks:
        if t.name in seen:
            continue
        seen.add(t.name)
        unique.append(t)
    return unique


def _alias_duplicates(tasks: List[TaskInfo]) -> Dict[str, List[str]]:
    alias_to_tasks: Dict[str, List[str]] = {}
    for task in tasks:
        for alias in task.aliases:
            alias_to_tasks.setdefault(alias, []).append(task.name)
    return {a: ts for a, ts in alias_to_tasks.items() if len(ts) > 1}


def _help_failures(
    pf_cmd: List[str],
    repo_root: Path,
    tasks: List[TaskInfo],
    timeout_s: int,
    jobs: int,
) -> List[Tuple[str, str]]:
    failures: List[Tuple[str, str]] = []

    def _check_one(task_name: str) -> Optional[Tuple[str, str]]:
        proc = _run([*pf_cmd, "help", task_name], repo_root=repo_root, timeout_s=timeout_s, capture_output=True)
        if proc.returncode == 0:
            return None
        msg = (proc.stderr or proc.stdout or "").strip()
        return task_name, msg[:500]

    with ThreadPoolExecutor(max_workers=max(1, jobs)) as pool:
        futures = {pool.submit(_check_one, t.name): t.name for t in tasks}
        for fut in as_completed(futures):
            res = fut.result()
            if res:
                failures.append(res)

    failures.sort(key=lambda x: x[0])
    return failures


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate pf tasks without executing them")
    parser.add_argument("--jobs", type=int, default=8, help="Parallelism for `pf help` checks (default: 8)")
    parser.add_argument("--timeout", type=int, default=30, help="Per-command timeout seconds (default: 30)")
    parser.add_argument("--skip-help-check", action="store_true", help="Skip `pf help <task>` for all tasks")
    parser.add_argument(
        "--use-system-pf",
        action="store_true",
        help="Use `pf` from PATH instead of the repo runner (default: prefer repo runner).",
    )
    args = parser.parse_args()

    repo_root = _repo_root()
    os.chdir(repo_root)

    print("\n🚀 Starting pf Task Validation (safe mode)")
    print("==================================================")

    pf_cmd = _pf_cmd(repo_root, use_system_pf=args.use_system_pf)
    print(f"🔍 Using runner: {' '.join(pf_cmd)}")

    # 1) Basic runner check
    proc = _run([*pf_cmd, "--help"], repo_root=repo_root, timeout_s=args.timeout)
    if proc.returncode != 0:
        print("❌ pf --help failed")
        print((proc.stderr or proc.stdout).strip())
        return 1
    print("✅ pf --help works")

    # 2) Syntax validation
    print("\n🔍 Running `pf prune` (syntax validation)...")
    proc = _run([*pf_cmd, "prune"], repo_root=repo_root, timeout_s=max(args.timeout, 120))
    if proc.returncode != 0:
        print("❌ pf prune failed")
        print((proc.stderr or proc.stdout).strip())
        return 1
    print("✅ pf prune passed")

    # 3) List + metadata validation
    print("\n🔍 Running `pf list` (metadata validation)...")
    proc = _run([*pf_cmd, "list"], repo_root=repo_root, timeout_s=args.timeout)
    if proc.returncode != 0:
        print("❌ pf list failed")
        print((proc.stderr or proc.stdout).strip())
        return 1

    tasks = _parse_pf_list(proc.stdout or "")
    if not tasks:
        print("❌ No tasks parsed from `pf list` output")
        return 1
    print(f"📊 Found {len(tasks)} tasks")

    no_desc = [t.name for t in tasks if not t.description]
    if no_desc:
        print(f"❌ {len(no_desc)} task(s) missing descriptions (example: {no_desc[:10]})")
        return 1
    print("✅ All tasks have descriptions")

    dup_aliases = _alias_duplicates(tasks)
    if dup_aliases:
        print(f"❌ Found {len(dup_aliases)} duplicate alias(es):")
        for alias, owners in sorted(dup_aliases.items()):
            print(f"  - {alias}: {', '.join(owners)}")
        return 1
    print("✅ No duplicate aliases")

    # 4) Help parseability
    if not args.skip_help_check:
        print("\n🔍 Running `pf help <task>` for every task...")
        failures = _help_failures(
            pf_cmd=pf_cmd,
            repo_root=repo_root,
            tasks=tasks,
            timeout_s=args.timeout,
            jobs=args.jobs,
        )
        if failures:
            print(f"❌ {len(failures)} task(s) failed `pf help`:")
            for task, msg in failures[:25]:
                print(f"  - {task}: {msg}")
            if len(failures) > 25:
                print(f"  ... plus {len(failures) - 25} more")
            return 1
        print("✅ All tasks are help-parseable")
    else:
        print("\nℹ️  Skipping `pf help <task>` checks")

    print("\n==================================================")
    print("✅ PF TASK VALIDATION PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
