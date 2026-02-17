#!/usr/bin/env python3
"""
Static pf task validation for this repo.

This script is intentionally non-destructive: it does not execute tasks.
It checks:
  - Pfyfile include targets exist
  - pf can load/parse the full task graph
  - obvious repo-relative paths referenced in `shell ...` lines exist
"""

from __future__ import annotations

import os
import shlex
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple


SCRIPT_LIKE_EXTS = (".sh", ".bash", ".zsh", ".py", ".mjs", ".pf")

INTERPRETERS = {"bash", "sh", "python3", "python", "node"}


@dataclass(frozen=True)
class Issue:
    kind: str
    message: str
    file: Optional[str] = None
    task: Optional[str] = None


def _repo_root_from_script() -> Path:
    return Path(__file__).resolve().parent.parent


def _load_pfyfiles(repo_root: Path) -> List[Path]:
    return sorted(repo_root.glob("Pfyfile*.pf"))


def _scan_includes(pfyfile: Path) -> List[str]:
    includes: List[str] = []
    inside_task = False
    for raw in pfyfile.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("task "):
            inside_task = True
        if inside_task:
            if line == "end":
                inside_task = False
            continue
        if line.startswith("include "):
            try:
                parts = shlex.split(line)
            except ValueError:
                parts = line.split()
            if len(parts) >= 2:
                includes.append(parts[1])
    return includes


def _validate_includes(repo_root: Path, pfyfiles: Sequence[Path]) -> List[Issue]:
    issues: List[Issue] = []
    for pfyfile in pfyfiles:
        base_dir = pfyfile.parent
        for inc in _scan_includes(pfyfile):
            inc_path = Path(inc)
            if not inc_path.is_absolute():
                inc_path = (base_dir / inc_path).resolve()
            if not inc_path.exists():
                issues.append(
                    Issue(
                        kind="include-missing",
                        message=f"Include not found: {inc} (resolved: {inc_path})",
                        file=str(pfyfile),
                    )
                )
    return issues


def _looks_dynamic(token: str) -> bool:
    return "$" in token or token.startswith("${") or token.startswith("$(")


def _normalize_token(token: str) -> str:
    return token.strip().strip(");,")


def _looks_like_script_path(token: str) -> bool:
    token = _normalize_token(token)
    if not token:
        return False
    if any(ch.isspace() for ch in token):
        # Quoted strings like "Security scanner: tools/x.mjs" should not be treated as paths.
        return False
    if _looks_dynamic(token):
        return False
    if token.startswith(("-", "--")):
        return False
    if token in {"&&", "||", "|", ";"}:
        return False
    return any(token.endswith(ext) for ext in SCRIPT_LIKE_EXTS)


def _extract_shell_cmd(line: str) -> Optional[str]:
    stripped = line.strip()
    if not stripped.startswith("shell "):
        return None
    cmd = stripped[6:].strip()
    if not cmd or cmd == "|":
        return None
    if cmd.startswith("|"):
        return None
    return cmd


def _validate_task_shell_paths(repo_root: Path, tasks: Dict[str, object]) -> List[Issue]:
    issues: List[Issue] = []

    for task_name, task_obj in tasks.items():
        source_file = getattr(task_obj, "source_file", None)
        task_dir = Path(source_file).resolve().parent if source_file else repo_root
        seen: set[Tuple[str, str]] = set()

        lines = getattr(task_obj, "lines", []) or []
        for line in lines:
            cmd = _extract_shell_cmd(line)
            if not cmd:
                continue

            try:
                tokens = shlex.split(cmd, posix=True)
            except ValueError:
                # Skip complex quoting; prune/grammar tests cover syntax validation.
                continue

            cwd = task_dir
            i = 0
            while i < len(tokens):
                tok = _normalize_token(tokens[i])

                # Track directory changes inside a single `shell ...` line.
                if tok == "cd" and i + 1 < len(tokens):
                    target = _normalize_token(tokens[i + 1])
                    if target and not _looks_dynamic(target) and not target.startswith("-"):
                        target_path = Path(target).expanduser()
                        cwd = target_path.resolve() if target_path.is_absolute() else (cwd / target_path).resolve()
                    i += 2
                    continue

                # Check interpreter-invoked scripts (e.g. `node tools/x.mjs`, `python3 tools/x.py`)
                if tok in INTERPRETERS:
                    j = i + 1
                    while j < len(tokens) and tokens[j].startswith("-"):
                        j += 1
                    if j < len(tokens) and _looks_like_script_path(tokens[j]):
                        script_token = _normalize_token(tokens[j])
                        script_path = Path(script_token).expanduser()
                        resolved = script_path.resolve() if script_path.is_absolute() else (cwd / script_path).resolve()
                        if not resolved.is_relative_to(repo_root):
                            i += 1
                            continue
                        key = (task_name, str(resolved))
                        if key in seen:
                            i += 1
                            continue
                        seen.add(key)
                        if not resolved.exists():
                            issues.append(
                                Issue(
                                    kind="path-missing",
                                    message=f"Missing script referenced by {tok}: {script_token} (resolved: {resolved})",
                                    file=str(source_file) if source_file else None,
                                    task=task_name,
                                )
                            )
                    i += 1
                    continue

                # Directly executed scripts (e.g. `./containers/scripts/foo.sh`)
                if _looks_like_script_path(tok) and (tok.startswith(("./", "../")) or "/" in tok):
                    script_path = Path(tok).expanduser()
                    resolved = script_path.resolve() if script_path.is_absolute() else (cwd / script_path).resolve()
                    if resolved.is_relative_to(repo_root):
                        key = (task_name, str(resolved))
                        if key not in seen:
                            seen.add(key)
                            if not resolved.exists():
                                issues.append(
                                    Issue(
                                        kind="path-missing",
                                        message=f"Missing script in shell command: {tok} (resolved: {resolved})",
                                        file=str(source_file) if source_file else None,
                                        task=task_name,
                                    )
                                )

                i += 1

    return issues


def _load_all_tasks(repo_root: Path, pfyfile_override: Optional[str]) -> Tuple[Dict[str, object], Optional[str]]:
    sys.path.insert(0, str(repo_root / "pf-runner"))
    import pf_config  # type: ignore
    import pf_parser  # type: ignore

    cfg, cfg_path = pf_config.load_config(start_dir=str(repo_root))
    pf_parser.configure(cfg, str(cfg_path) if cfg_path else None)

    dsl_src, task_sources = pf_parser._load_pfy_source_with_includes(file_arg=pfyfile_override)
    tasks = pf_parser.parse_pfyfile_text(dsl_src, task_sources)
    return tasks, str(cfg_path) if cfg_path else None


def main(argv: Sequence[str]) -> int:
    repo_root = _repo_root_from_script()

    pfyfile_override = None
    if len(argv) >= 2 and argv[1].startswith("--file="):
        pfyfile_override = argv[1].split("=", 1)[1]
    elif len(argv) >= 3 and argv[1] == "--file":
        pfyfile_override = argv[2]

    pfyfiles = _load_pfyfiles(repo_root)
    if not pfyfiles:
        print("No Pfyfile*.pf files found at repo root.", file=sys.stderr)
        return 1

    issues: List[Issue] = []
    issues.extend(_validate_includes(repo_root, pfyfiles))

    tasks: Dict[str, object]
    cfg_path: Optional[str]
    try:
        tasks, cfg_path = _load_all_tasks(repo_root, pfyfile_override)
    except Exception as e:
        issues.append(Issue(kind="load-failed", message=f"Failed to load/parse tasks: {e}"))
        tasks = {}
        cfg_path = None

    if tasks:
        issues.extend(_validate_task_shell_paths(repo_root, tasks))

    errors = [i for i in issues if i.kind in {"include-missing", "path-missing", "load-failed"}]

    print("pf task validation")
    print(f"- repo: {repo_root}")
    print(f"- config: {cfg_path or 'defaults'}")
    print(f"- pfyfiles: {len(pfyfiles)}")
    print(f"- tasks: {len(tasks)}")
    print(f"- issues: {len(issues)} (errors: {len(errors)})")

    if issues:
        print("\nIssues:")
        for issue in issues[:200]:
            loc = []
            if issue.file:
                loc.append(issue.file)
            if issue.task:
                loc.append(f"task={issue.task}")
            where = f" [{', '.join(loc)}]" if loc else ""
            print(f"- {issue.kind}{where}: {issue.message}")

        if len(issues) > 200:
            print(f"... truncated ({len(issues) - 200} more)")

    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
