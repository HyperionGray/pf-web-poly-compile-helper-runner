#!/usr/bin/env python3
"""
pf_config.py - Central config loader for pf-runner and repo scripts.

The project uses a single JSON5 config file (default: pf.config.json5) and avoids
PF_* environment variables for configuration.
"""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

try:
    import json5  # type: ignore
except Exception:  # pragma: no cover - best-effort import for minimal environments
    json5 = None


DEFAULT_CONFIG_FILENAME = "pf.config.json5"

DEFAULT_CONFIG: Dict[str, Any] = {
    "pfy": {
        "file": "Pfyfile.pf",
        "searchParents": "git",  # git|all|none
    },
    "runner": {
        "autocorrect": {
            "mode": "auto",  # auto|ask|off
            "threshold": 0.75,
        },
        "pathAutofix": True,
        "playwright": {
            "headful": False,
        },
    },
    "api": {
        "host": "127.0.0.1",
        "port": 8000,
        "workers": 4,
    },
    "container": {
        "runtime": "podman",
        "image": "localhost/pf-runner:latest",
    },
    "devEnvironment": {
        "useQuadlet": True,
        "gpuSupport": False,
    },
    "os": {
        "distroArtifactsDir": "~/.pf/distros",
        "switchBaseDir": "~/.pf/os-switch",
    },
}


def _deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    out = dict(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(out.get(key), dict):
            out[key] = _deep_merge(out[key], value)  # type: ignore[arg-type]
        else:
            out[key] = value
    return out


def _git_root(start_dir: Path) -> Optional[Path]:
    cur = start_dir.resolve()
    while True:
        if (cur / ".git").exists():
            return cur
        parent = cur.parent
        if parent == cur:
            return None
        cur = parent


def find_config_path(start_dir: Optional[str] = None, explicit_path: Optional[str] = None) -> Optional[Path]:
    start = Path(start_dir).resolve() if start_dir else Path.cwd().resolve()

    if explicit_path:
        explicit = Path(explicit_path).expanduser()
        if not explicit.is_absolute():
            explicit = (start / explicit).resolve()
        return explicit

    stop = _git_root(start) or Path(start.anchor)
    cur = start
    while True:
        candidate = cur / DEFAULT_CONFIG_FILENAME
        if candidate.is_file():
            return candidate
        if cur == stop or cur.parent == cur:
            break
        cur = cur.parent

    # User config fallbacks
    home = Path.home()
    for candidate in (
        home / ".config" / "pf" / DEFAULT_CONFIG_FILENAME,
        home / ".pf" / DEFAULT_CONFIG_FILENAME,
    ):
        if candidate.is_file():
            return candidate

    # Installed fallback: config alongside pf-runner sources (e.g. /usr/local/lib/pf-runner)
    installed_candidate = Path(__file__).resolve().parent / DEFAULT_CONFIG_FILENAME
    if installed_candidate.is_file():
        return installed_candidate

    return None


def load_config(
    *,
    start_dir: Optional[str] = None,
    explicit_path: Optional[str] = None,
    require_exists: bool = False,
) -> Tuple[Dict[str, Any], Optional[Path]]:
    """
    Load config and return (config_dict, resolved_path).

    If require_exists=True and the resolved path does not exist, raises FileNotFoundError.
    """
    resolved = find_config_path(start_dir=start_dir, explicit_path=explicit_path)
    if resolved is None:
        return deepcopy(DEFAULT_CONFIG), None

    if not resolved.is_file():
        if require_exists:
            raise FileNotFoundError(f"Config file not found: {resolved}")
        return deepcopy(DEFAULT_CONFIG), resolved

    raw = resolved.read_text(encoding="utf-8")
    if json5 is None:
        raise RuntimeError(
            "JSON5 parsing is unavailable (missing python 'json5' package). "
            "Install it or use a strict JSON file."
        )
    parsed = json5.loads(raw)
    if not isinstance(parsed, dict):
        raise ValueError(f"Config root must be an object: {resolved}")

    merged = _deep_merge(deepcopy(DEFAULT_CONFIG), parsed)
    return merged, resolved


def get(cfg: Dict[str, Any], dotted_key: str, default: Any = None) -> Any:
    cur: Any = cfg
    for part in dotted_key.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return default
        cur = cur[part]
    return cur


def get_bool(cfg: Dict[str, Any], dotted_key: str, default: bool) -> bool:
    value = get(cfg, dotted_key, default)
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "on"}
    return default


def get_int(cfg: Dict[str, Any], dotted_key: str, default: int) -> int:
    value = get(cfg, dotted_key, default)
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        try:
            return int(value.strip(), 10)
        except Exception:
            return default
    return default


def get_float(cfg: Dict[str, Any], dotted_key: str, default: float) -> float:
    value = get(cfg, dotted_key, default)
    if isinstance(value, (float, int)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value.strip())
        except Exception:
            return default
    return default


def resolve_path(value: str, *, base_dir: Optional[Path] = None) -> str:
    expanded = Path(value).expanduser()
    if expanded.is_absolute():
        return str(expanded)
    if base_dir:
        return str((base_dir / expanded).resolve())
    return str(expanded)
