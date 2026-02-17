#!/usr/bin/env python3
"""
pf_parser_config.py - Configuration and Pfyfile discovery helpers.
"""

import os
from typing import Optional, Dict, Any, List

import pf_config

# ---------- CONFIG ----------
_PF_CONFIG: Optional[Dict[str, Any]] = None
_PF_CONFIG_PATH: Optional[str] = None

PFY_FILE = "Pfyfile.pf"
PFY_SEARCH_PARENTS = "git"  # git|all|none
PFY_ROOT: Optional[str] = None  # Set by main() when loading the Pfyfile
ENV_MAP: Dict[str, List[str] | str] = {
    "local": ["@local"],
    "prod": ["ubuntu@10.0.0.5:22", "punk@10.4.4.4:24"],
    "staging": "staging@10.1.2.3:22,staging@10.1.2.4:22",
}

# Embedded default tasks when no Pfyfile is found
PFY_EMBED = """
# Default embedded tasks - shown when no Pfyfile is found
"""


def configure(config: Optional[Dict[str, Any]] = None, config_path: Optional[str] = None) -> None:
    """
    Configure pf_parser defaults from the central JSON5 config.

    The caller (pf_main) should prefer passing an already-loaded config dict.
    """
    global _PF_CONFIG, _PF_CONFIG_PATH, PFY_FILE, PFY_SEARCH_PARENTS

    if config is None:
        cfg, resolved = pf_config.load_config(start_dir=os.getcwd(), explicit_path=config_path)
        _PF_CONFIG = cfg
        _PF_CONFIG_PATH = str(resolved) if resolved else None
    else:
        _PF_CONFIG = config
        _PF_CONFIG_PATH = config_path

    PFY_FILE = pf_config.get(_PF_CONFIG, "pfy.file", "Pfyfile.pf") or "Pfyfile.pf"
    PFY_SEARCH_PARENTS = pf_config.get(_PF_CONFIG, "pfy.searchParents", "git") or "git"


def _ensure_config_loaded() -> None:
    if _PF_CONFIG is None:
        configure()


# ---------- Pfyfile discovery ----------
def _pfy_search_mode() -> str:
    """
    Control how pf discovers a Pfyfile when no explicit file is provided.

    Config:
      pfy.searchParents:
        - "git" (default): search upwards but stop at the git repo root (directory containing .git)
        - "all": search upwards to the filesystem root
        - "none": do not search parent directories (only check start_dir/cwd)
    """
    _ensure_config_loaded()
    raw = (PFY_SEARCH_PARENTS or "git").strip().lower()
    if raw in {"0", "false", "no", "off", "none"}:
        return "none"
    if raw in {"1", "true", "yes", "on", "all"}:
        return "all"
    return "git"


def _git_root(start_dir: str) -> Optional[str]:
    """Best-effort detection of git repo root (supports .git dir or file)."""
    cur = os.path.abspath(start_dir)
    while True:
        if os.path.exists(os.path.join(cur, ".git")):
            return cur
        parent = os.path.dirname(cur)
        if parent == cur:
            return None
        cur = parent


def _find_pfyfile(start_dir: Optional[str] = None, file_arg: Optional[str] = None) -> str:
    cur = os.path.abspath(start_dir or os.getcwd())

    if file_arg:
        file_arg = os.path.expanduser(os.path.expandvars(file_arg))
        if os.path.isabs(file_arg):
            return file_arg
        return os.path.abspath(os.path.join(cur, file_arg))

    _ensure_config_loaded()
    pf_hint = PFY_FILE or "Pfyfile.pf"
    pf_hint = os.path.expanduser(os.path.expandvars(pf_hint))
    if os.path.isabs(pf_hint):
        return pf_hint

    direct = os.path.join(cur, pf_hint)
    if os.path.isfile(direct):
        return os.path.abspath(direct)

    # If the config lives alongside a Pfyfile, prefer that when not in a repo.
    if _PF_CONFIG_PATH:
        cfg_dir = os.path.dirname(os.path.abspath(_PF_CONFIG_PATH))
        cfg_candidate = os.path.join(cfg_dir, pf_hint)
        if os.path.isfile(cfg_candidate):
            return os.path.abspath(cfg_candidate)

    mode = _pfy_search_mode()
    if mode == "none":
        return os.path.abspath(direct)

    stop_dir = None
    if mode == "git":
        stop_dir = _git_root(cur)
        # In the default "git" mode, avoid searching parent directories when the
        # caller is not inside a git repo. This prevents surprising cross-project
        # Pfyfile discovery (and expensive filesystem walks).
        if stop_dir is None:
            return os.path.abspath(direct)

    walk = cur
    while True:
        candidate = os.path.join(walk, pf_hint)
        if os.path.isfile(candidate):
            return os.path.abspath(candidate)

        if stop_dir and walk == stop_dir:
            return os.path.abspath(direct)

        parent = os.path.dirname(walk)
        if parent == walk:
            return os.path.abspath(direct)
        walk = parent
