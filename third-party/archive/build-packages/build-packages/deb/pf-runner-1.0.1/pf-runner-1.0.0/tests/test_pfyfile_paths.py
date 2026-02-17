#!/usr/bin/env python3
"""
Path/layout guardrails for Pfyfiles.

This repo convention is:
  - No Pfyfile*.pf at repo root
  - Real Pfyfiles live under pf-files/ (organized by category)

This test is intentionally dependency-free (stdlib only) and should catch:
  - Broken/missing include targets
  - Accidental re-introduction of root-level Pfyfiles
"""

from __future__ import annotations

import shlex
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class IncludeRef:
    source: Path
    line_no: int
    target_raw: str
    target_resolved: Path


def _repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _iter_includes(pfyfile: Path) -> list[IncludeRef]:
    refs: list[IncludeRef] = []
    inside_task = False

    try:
        lines = pfyfile.read_text(encoding="utf-8").splitlines()
    except UnicodeDecodeError:
        lines = pfyfile.read_text(encoding="utf-8", errors="replace").splitlines()

    for idx, raw in enumerate(lines, start=1):
        stripped = raw.strip()
        if stripped.startswith("task "):
            inside_task = True
            continue
        if stripped == "end":
            inside_task = False
            continue
        if inside_task:
            continue
        if not stripped.startswith("include "):
            continue

        try:
            toks = shlex.split(stripped)
        except ValueError:
            toks = stripped.split()
        if len(toks) < 2:
            continue

        target = toks[1]
        resolved = Path(target)
        if not resolved.is_absolute():
            resolved = (pfyfile.parent / resolved).resolve()

        refs.append(
            IncludeRef(
                source=pfyfile,
                line_no=idx,
                target_raw=target,
                target_resolved=resolved,
            )
        )

    return refs


def _walk_include_graph(entry: Path) -> tuple[set[Path], list[IncludeRef]]:
    visited: set[Path] = set()
    missing: list[IncludeRef] = []

    def visit(path: Path) -> None:
        resolved = path.resolve()
        if resolved in visited:
            return
        visited.add(resolved)

        for inc in _iter_includes(resolved):
            if not inc.target_resolved.exists():
                missing.append(inc)
                continue
            visit(inc.target_resolved)

    visit(entry)
    return visited, missing


def main() -> int:
    print("🔎 Pfyfile path/layout validation")

    repo_root = _repo_root()
    print(f"📁 Repo root: {repo_root}")

    root_pfyfiles = sorted(repo_root.glob("Pfyfile*.pf"))
    if root_pfyfiles:
        print("❌ Found root-level Pfyfiles (expected none):")
        for path in root_pfyfiles:
            print(f"  - {path.relative_to(repo_root)}")
        return 1
    print("✅ No root-level Pfyfiles found")

    required = [
        repo_root / "pf-files" / "Pfyfile.pf",
        repo_root / "pf-files" / "always-available" / "Pfyfile.always-available.pf",
    ]
    missing_required = [p for p in required if not p.exists()]
    if missing_required:
        print("❌ Missing required Pfyfiles:")
        for path in missing_required:
            print(f"  - {path.relative_to(repo_root)}")
        return 1

    all_missing: list[IncludeRef] = []
    for entry in required:
        print(f"🔗 Validating include graph from: {entry.relative_to(repo_root)}")
        _visited, missing = _walk_include_graph(entry)
        all_missing.extend(missing)

    if all_missing:
        print("❌ Missing include targets:")
        for inc in all_missing:
            try:
                rel_source = inc.source.relative_to(repo_root)
            except ValueError:
                rel_source = inc.source
            try:
                rel_target = inc.target_resolved.relative_to(repo_root)
            except ValueError:
                rel_target = inc.target_resolved
            print(f"  - {rel_source}:{inc.line_no} include {inc.target_raw} -> {rel_target}")
        return 1

    print("✅ All include targets exist")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

