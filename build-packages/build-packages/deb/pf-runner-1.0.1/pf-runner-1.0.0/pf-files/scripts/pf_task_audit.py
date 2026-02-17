#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
import signal
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple


@dataclass(frozen=True)
class TaskInfo:
    name: str
    source: Optional[str]
    description: Optional[str]
    aliases: List[str]
    default_params: Dict[str, str]
    lines: List[str]


def _repo_root_from_script() -> Path:
    here = Path(__file__).resolve()
    for candidate in [here.parent, *here.parents]:
        if (candidate / "pf-runner-full").is_dir() and (candidate / "pf-files").is_dir():
            return candidate
    # Fallback: best-effort
    return here.parents[1]


def _load_tasks(repo_root: Path) -> List[TaskInfo]:
    sys.path.insert(0, str(repo_root / "pf-runner-full"))
    from pf_parser import _load_pfy_source_with_includes, parse_pfyfile_text  # type: ignore

    text, sources = _load_pfy_source_with_includes(file_arg=None)
    tasks = parse_pfyfile_text(text, sources)
    out: List[TaskInfo] = []
    for name, task in sorted(tasks.items()):
        out.append(
            TaskInfo(
                name=name,
                source=getattr(task, "source_file", None),
                description=getattr(task, "description", None),
                aliases=list(getattr(task, "aliases", []) or []),
                default_params=dict(getattr(task, "params", {}) or {}),
                lines=list(getattr(task, "lines", []) or []),
            )
        )
    return out


def _safe_filename(s: str) -> str:
    s = s.strip().replace(os.sep, "_")
    s = re.sub(r"[^A-Za-z0-9._-]+", "_", s)
    return s[:180] if len(s) > 180 else s


def _detect_danger(task: TaskInfo) -> Optional[str]:
    if task.source and task.source.endswith("pf-files/distro-switching/Pfyfile.os-switching.pf"):
        return "dangerous: os-switching"

    # Heuristic scan for obviously destructive operations.
    joined = "\n".join(task.lines)
    danger_patterns = [
        r"\bkexec\b",
        r"\bmkfs\.",
        r"\bdd\s+if=",
        r"\bgrub-(install|mkconfig)\b",
        r"\bbtrfs\s+subvolume\s+snapshot\b",
        r"\bzfs\s+snapshot\b",
        r"\brsync\s+-aAX\b.*\s/\s",
    ]
    for pat in danger_patterns:
        if re.search(pat, joined):
            return f"dangerous: pattern {pat}"
    return None


def _classify_failure(log_text: str) -> Optional[str]:
    t = log_text
    if re.search(r"\bcommand not found\b", t):
        return "missing_command"
    if re.search(r"No such file or directory", t):
        return "missing_path"
    if re.search(r"\bUsage:\b", t) or re.search(r"\bparameter required\b", t, re.IGNORECASE):
        return "usage_or_missing_param"
    if re.search(r"\bpermission denied\b", t, re.IGNORECASE):
        return "permission_denied"
    return None


def _read_tail(path: Path, max_bytes: int = 120_000) -> str:
    try:
        data = path.read_bytes()
    except FileNotFoundError:
        return ""
    if len(data) <= max_bytes:
        return data.decode("utf-8", errors="replace")
    return data[-max_bytes:].decode("utf-8", errors="replace")


def _run_with_timeout(
    cmd: List[str],
    *,
    cwd: Path,
    env: Dict[str, str],
    timeout_s: int,
    log_path: Path,
) -> Tuple[int, float, bool]:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    start = time.time()
    timed_out = False

    with log_path.open("wb") as f:
        f.write(f"$ {' '.join(cmd)}\n".encode())
        f.flush()

        proc = subprocess.Popen(
            cmd,
            cwd=str(cwd),
            env=env,
            stdout=f,
            stderr=subprocess.STDOUT,
            start_new_session=True,  # lets us kill the whole process group
        )
        try:
            rc = proc.wait(timeout=timeout_s)
        except subprocess.TimeoutExpired:
            timed_out = True
            # Kill the whole process group.
            try:
                os.killpg(proc.pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
            try:
                rc = proc.wait(timeout=3)
            except subprocess.TimeoutExpired:
                try:
                    os.killpg(proc.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                rc = proc.wait()

    duration = time.time() - start
    return int(rc), float(duration), timed_out


def main(argv: List[str]) -> int:
    repo_root = _repo_root_from_script()
    default_pf = repo_root / "pf-runner-full" / "pf_universal"

    ap = argparse.ArgumentParser(description="Smoke-run pf tasks and record failures.")
    ap.add_argument("--pf", default=str(default_pf), help="Path to pf executable (default: pf-runner-full/pf_universal)")
    ap.add_argument("--cwd", default=str(repo_root), help="Working directory to run tasks from (default: repo root)")
    ap.add_argument("--timeout", type=int, default=5, help="Per-task timeout seconds (default: 5)")
    ap.add_argument("--max-tasks", type=int, default=0, help="Limit number of tasks (0 = all)")
    ap.add_argument("--include", default="", help="Only run tasks matching this regex")
    ap.add_argument("--exclude", default="", help="Skip tasks matching this regex")
    ap.add_argument(
        "--out-dir",
        default=str(repo_root / "pf-files" / "task-audit"),
        help="Output directory (default: pf-files/task-audit)",
    )
    args = ap.parse_args(argv)

    pf_path = Path(args.pf).resolve()
    cwd = Path(args.cwd).resolve()
    out_dir = Path(args.out_dir).resolve()
    logs_dir = out_dir / "logs"
    out_dir.mkdir(parents=True, exist_ok=True)

    tasks = _load_tasks(repo_root)

    include_re = re.compile(args.include) if args.include else None
    exclude_re = re.compile(args.exclude) if args.exclude else None

    # Provide a "pf" shim in PATH so tasks that call `pf ...` work during audit.
    shim_dir = out_dir / "bin"
    shim_dir.mkdir(parents=True, exist_ok=True)
    shim_pf = shim_dir / "pf"
    if shim_pf.exists() or shim_pf.is_symlink():
        shim_pf.unlink()
    shim_pf.symlink_to(pf_path)

    env = dict(os.environ)
    env["PATH"] = str(shim_dir) + os.pathsep + env.get("PATH", "")
    env.setdefault("CI", "1")

    results: List[Dict[str, Any]] = []
    ran = 0
    for idx, task in enumerate(tasks, start=1):
        if include_re and not include_re.search(task.name):
            continue
        if exclude_re and exclude_re.search(task.name):
            continue
        if args.max_tasks and ran >= args.max_tasks:
            break

        danger = _detect_danger(task)
        log_name = f"{idx:04d}-{_safe_filename(task.name)}.log"
        log_path = logs_dir / log_name

        if danger:
            results.append(
                {
                    "task": task.name,
                    "source": task.source,
                    "description": task.description,
                    "aliases": task.aliases,
                    "default_params": task.default_params,
                    "status": "skipped",
                    "skip_reason": danger,
                    "exit_code": None,
                    "duration_s": 0.0,
                    "timed_out": False,
                    "log": str(log_path),
                }
            )
            continue

        cmd = [str(pf_path), "run", task.name]
        rc, dur, timed_out = _run_with_timeout(
            cmd,
            cwd=cwd,
            env=env,
            timeout_s=args.timeout,
            log_path=log_path,
        )
        tail = _read_tail(log_path)
        fail_class = None if (rc == 0 and not timed_out) else _classify_failure(tail)
        status = "ok" if (rc == 0 and not timed_out) else ("timeout" if timed_out else "fail")

        results.append(
            {
                "task": task.name,
                "source": task.source,
                "description": task.description,
                "aliases": task.aliases,
                "default_params": task.default_params,
                "status": status,
                "exit_code": rc,
                "duration_s": round(dur, 3),
                "timed_out": timed_out,
                "failure_class": fail_class,
                "log": str(log_path),
            }
        )
        ran += 1

    results_path = out_dir / "results.json"
    results_path.write_text(json.dumps(results, indent=2), encoding="utf-8")

    # Human summary
    totals = {"ok": 0, "fail": 0, "timeout": 0, "skipped": 0}
    by_class: Dict[str, int] = {}
    for r in results:
        totals[r["status"]] += 1
        fc = r.get("failure_class")
        if fc:
            by_class[fc] = by_class.get(fc, 0) + 1

    summary_lines = []
    summary_lines.append("# pf task audit (smoke run)")
    summary_lines.append("")
    summary_lines.append(f"- cwd: `{cwd}`")
    summary_lines.append(f"- pf: `{pf_path}`")
    summary_lines.append(f"- timeout: `{args.timeout}s`")
    summary_lines.append(f"- tasks total (loaded): `{len(tasks)}`")
    summary_lines.append(f"- tasks evaluated: `{len(results)}`")
    summary_lines.append("")
    summary_lines.append("## Results")
    summary_lines.append("")
    for k in ("ok", "fail", "timeout", "skipped"):
        summary_lines.append(f"- {k}: `{totals[k]}`")
    if by_class:
        summary_lines.append("")
        summary_lines.append("## Failures by class")
        summary_lines.append("")
        for k, v in sorted(by_class.items(), key=lambda kv: (-kv[1], kv[0])):
            summary_lines.append(f"- {k}: `{v}`")
    summary_lines.append("")
    summary_lines.append("## Notes")
    summary_lines.append("")
    summary_lines.append("- `timeout` means the task did not finish within the configured time; it may still be fine (e.g. servers, installers).")
    summary_lines.append("- `skipped` means the task matched a safety heuristic (e.g. OS switching).")
    summary_lines.append("")
    (out_dir / "SUMMARY.md").write_text("\n".join(summary_lines) + "\n", encoding="utf-8")

    print(f"Wrote `{results_path}` and `{out_dir / 'SUMMARY.md'}`")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
