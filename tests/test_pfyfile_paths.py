#!/usr/bin/env python3
"""
Path/layout guardrails for Pfyfiles.

This repo convention is:
  - Canonical Pfyfiles live under pf-files/ (organized by category)
  - A root Pfyfile.pf compatibility entrypoint is allowed if it delegates to pf-files/Pfyfile.pf
  - No additional root-level Pfyfile*.pf files are allowed

This test is intentionally dependency-free (stdlib only) and should catch:
  - Broken/missing include targets
  - Unexpected root-level Pfyfiles
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
    compatibility_entry = repo_root / "Pfyfile.pf"
    unexpected_root_pfyfiles = [path for path in root_pfyfiles if path != compatibility_entry]

    if unexpected_root_pfyfiles:
        print("❌ Found unexpected root-level Pfyfiles:")
        for path in unexpected_root_pfyfiles:
            print(f"  - {path.relative_to(repo_root)}")
        return 1

    if compatibility_entry.exists():
        content = compatibility_entry.read_text(encoding="utf-8", errors="replace")
        if "include pf-files/Pfyfile.pf" not in content:
            print("❌ Root compatibility Pfyfile does not delegate to pf-files/Pfyfile.pf")
            return 1
        print("✅ Root compatibility Pfyfile delegates to pf-files/Pfyfile.pf")
    else:
        print("✅ No root compatibility Pfyfile found")

    legacy_multi_exec = repo_root / "pf-files" / "multi-exec"
    if legacy_multi_exec.exists():
        print("🔁 Validating legacy multi-exec compatibility shims")
        expected_shims = {
            "Pfyfile.pe-containers.pf": "include ../mult-exec/Pfyfile.pe-containers.pf",
            "Pfyfile.pe-execution.pf": "include ../mult-exec/Pfyfile.pe-execution.pf",
        }
        actual_legacy_files = sorted(path.name for path in legacy_multi_exec.glob("Pfyfile*.pf"))
        if actual_legacy_files != sorted(expected_shims):
            print("❌ Legacy multi-exec directory contains unexpected files:")
            for name in actual_legacy_files:
                print(f"  - {name}")
            return 1

        for name, include_line in expected_shims.items():
            shim_path = legacy_multi_exec / name
            shim_text = shim_path.read_text(encoding="utf-8", errors="replace")
            if include_line not in shim_text:
                print(f"❌ Legacy shim does not delegate to canonical mult-exec file: {shim_path.relative_to(repo_root)}")
                return 1
            if "task " in shim_text:
                print(f"❌ Legacy shim contains task definitions instead of delegating cleanly: {shim_path.relative_to(repo_root)}")
                return 1

        print("✅ Legacy multi-exec compatibility shims delegate to mult-exec")

    pe_module = repo_root / "pf-files" / "Pfyfile.pe.pf"
    pe_module_text = pe_module.read_text(encoding="utf-8", errors="replace")
    if 'pf "$MODULE_DIR/mult-exec/Pfyfile.pe-containers.pf" pe-reactos-run pe="${pe_file}"' not in pe_module_text:
        print("❌ PE module wrapper does not dispatch execute-reactos through the canonical mult-exec ReactOS task")
        return 1
    if 'pf "$MODULE_DIR/multi-exec/' in pe_module_text:
        print("❌ PE module wrapper still references the stale multi-exec path")
        return 1
    print("✅ PE module wrapper dispatches through the canonical mult-exec tasks")

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

