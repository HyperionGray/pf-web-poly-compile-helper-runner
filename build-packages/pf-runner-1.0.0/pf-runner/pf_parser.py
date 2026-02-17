#!/usr/bin/env python3
"""
pf_parser.py - Core DSL parser and task runner for pf

This module is the heart of the pf task runner, providing:
- Symbol-free DSL: shell, packages install/remove, service start/stop/enable/disable/restart, directory, copy
- describe: one-line task description shows in `pf list`
- include: top-level includes (outside tasks) to split stacks
- Per-task params: pf run-tls tls_cert=... tls_key=... port=9443 (use $tls_cert in DSL)
- Per-task env: inside a task, `env KEY=VAL KEY2=VAL2` applies to subsequent lines in that task
- Envs/hosts: env=prod, hosts=user@ip:port,..., repeatable host=...
- Parallel SSH across hosts with prefixed live output
- Flexible help: support help, --help, -h, hlep, hepl, heelp, hlp variations
- Flexible parameters: --key=value, -k val, and key=value are equivalent

File Structure (split into focused modules):
  - pf_parser_config.py: configuration + Pfyfile discovery
  - pf_parser_utils.py: interpolation helpers
  - pf_parser_polyglot_helpers.py: polyglot execution helpers
  - pf_dsl_parser.py: task parsing / DSL rules
  - pf_parser.py: includes, hosts, execution, and CLI glue

Install
  pip install "fabric>=3.2,<4"

Usage
  pf list
  pf [env=prod]* [hosts=..|host=..]* [user=..] [port=..] [sudo=true] [sudo_user=..] <task> [k=v ...] [next_task [k=v ...]]...
"""

import os
import sys
import shlex
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Tuple, Optional, Any

import pf_parser_config as _config
from pf_parser_utils import _interpolate
from pf_parser_polyglot_helpers import (
    _LANG_BRACKET_RE,
    _extract_polyglot_heredoc,
    _render_polyglot_command,
)
from pf_dsl_parser import Task, parse_pfyfile_text, _parse_task_definition

# Add bundled fabric to path if available
_script_dir = os.path.dirname(os.path.abspath(__file__))
_bundled_fabric = os.path.join(_script_dir, "fabric")
if os.path.isdir(_bundled_fabric) and _bundled_fabric not in sys.path:
    sys.path.insert(0, os.path.dirname(_bundled_fabric))

from fabric import Connection

# Import custom exceptions
try:
    from pf_exceptions import (
        PFException,
        PFSyntaxError,
        PFExecutionError,
        PFEnvironmentError,
        PFConnectionError,
        PFTaskNotFoundError,
        format_exception_for_user
    )
except ImportError:
    # If exceptions module not available, define minimal versions
    class PFException(Exception):
        pass
    class PFSyntaxError(PFException):
        pass
    class PFExecutionError(PFException):
        pass
    class PFEnvironmentError(PFException):
        pass
    class PFConnectionError(PFException):
        pass
    class PFTaskNotFoundError(PFException):
        pass
    def format_exception_for_user(exc, include_traceback=True):
        return str(exc)

def _sync_config_globals() -> None:
    global PFY_FILE, PFY_SEARCH_PARENTS, PFY_ROOT, ENV_MAP, PFY_EMBED
    PFY_FILE = _config.PFY_FILE
    PFY_SEARCH_PARENTS = _config.PFY_SEARCH_PARENTS
    PFY_ROOT = _config.PFY_ROOT
    ENV_MAP = _config.ENV_MAP
    PFY_EMBED = _config.PFY_EMBED


def configure(config: Optional[Dict[str, Any]] = None, config_path: Optional[str] = None) -> None:
    _config.configure(config=config, config_path=config_path)
    _sync_config_globals()


def _ensure_config_loaded() -> None:
    _config._ensure_config_loaded()
    _sync_config_globals()


def _find_pfyfile(start_dir: Optional[str] = None, file_arg: Optional[str] = None) -> str:
    return _config._find_pfyfile(start_dir=start_dir, file_arg=file_arg)


_pfy_search_mode = _config._pfy_search_mode
_git_root = _config._git_root


_sync_config_globals()

# Import HELP_VARIATIONS from pf_args to avoid duplication
try:
    from pf_args import HELP_VARIATIONS
except ImportError:
    # Fallback for standalone use
    HELP_VARIATIONS = {
        "help",
        "--help",
        "-h",
        "hlep",
        "hepl",
        "heelp",
        "hlp",
        "--hlep",
        "--hepl",
        "--heelp",
        "--hlp",
    }

# Built-in task definitions (kept empty unless populated elsewhere).
BUILTINS: Dict[str, List[str]] = {}


# ---------- DSL (include + describe) ----------
def _read_text_file(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def _expand_includes_from_text(
    text: str, base_dir: str, visited: set[str], current_file: Optional[str] = None
) -> Tuple[str, Dict[str, str]]:
    """Expand includes and track which file each task came from.
    Returns: (expanded_text, task_name_to_source_file_map)
    """
    out_lines: List[str] = []
    task_sources: Dict[str, str] = {}
    inside_task = False
    current_task_name = None

    for raw in text.splitlines():
        line = raw.rstrip("\n")
        stripped = line.strip()
        if stripped.startswith("task "):
            inside_task = True
            # Parse task name only (without parameters)
            try:
                task_name, _, _ = _parse_task_definition(stripped)
            except ValueError:
                task_name = (
                    stripped.split(None, 1)[1].strip()
                    if len(stripped.split()) > 1
                    else ""
                )
            current_task_name = task_name
            # Track the source file for this task (use current_file if in an include)
            if current_file:
                task_sources[task_name] = current_file
            out_lines.append(line)
            continue
        if stripped == "end":
            inside_task = False
            current_task_name = None
            out_lines.append(line)
            continue
        if not inside_task and stripped.startswith("include "):
            try:
                toks = shlex.split(stripped)
            except ValueError:
                toks = stripped.split()
            if len(toks) >= 2:
                inc_path = toks[1]
                inc_full = (
                    inc_path
                    if os.path.isabs(inc_path)
                    else os.path.join(base_dir, inc_path)
                )
                inc_full = os.path.normpath(inc_full)
                if inc_full in visited:
                    continue
                if not os.path.exists(inc_full):
                    print(f"[warn] include file not found: {inc_full}", file=sys.stderr)
                    continue
                visited.add(inc_full)
                inc_text = _read_text_file(inc_full)

                # Process included file with its path as current_file
                inc_expanded, inc_sources = _expand_includes_from_text(
                    inc_text, os.path.dirname(inc_full), visited, inc_full
                )

                # Merge task sources
                task_sources.update(inc_sources)

                out_lines.append(f"# --- begin include: {inc_full} ---")
                out_lines.append(inc_expanded)
                out_lines.append(f"# --- end include: {inc_full} ---")
                continue
        out_lines.append(line)
    return (
        "\n".join(out_lines)
        + ("\n" if out_lines and not out_lines[-1].endswith("\n") else ""),
        task_sources,
    )


def _load_pfy_source_with_includes(
    file_arg: Optional[str] = None,
) -> Tuple[str, Dict[str, str]]:
    """Load Pfyfile with includes expanded, return (text, task_sources)
    
    Always includes Pfyfile.always-available.pf which contains context-free
    tasks that work from any directory (TUI, tool installation, etc.)
    """
    # Load always-available tasks first
    # Find the always-available file relative to this script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    always_available_path = os.path.join(
        os.path.dirname(script_dir), "Pfyfile.always-available.pf"
    )
    if not os.path.exists(always_available_path):
        alt_path = os.path.join(script_dir, "Pfyfile.always-available.pf")
        if os.path.exists(alt_path):
            always_available_path = alt_path
    
    always_available_text = ""
    always_available_sources = {}
    if os.path.exists(always_available_path):
        always_available_text = _read_text_file(always_available_path)
        # Expand includes within always-available file
        always_visited: set[str] = {os.path.abspath(always_available_path)}
        always_available_text, always_available_sources = _expand_includes_from_text(
            always_available_text,
            os.path.dirname(always_available_path),
            always_visited,
            always_available_path  # current_file parameter
        )
    
    # Now load the user's Pfyfile (or fallback)
    pfy_resolved = _find_pfyfile(file_arg=file_arg)
    if os.path.exists(pfy_resolved):
        _config.PFY_ROOT = os.path.dirname(os.path.abspath(pfy_resolved)) or os.getcwd()
        _sync_config_globals()
        os.environ.setdefault("PFY_ROOT", _config.PFY_ROOT)
        base_dir = os.path.dirname(os.path.abspath(pfy_resolved)) or "."
        visited: set[str] = {os.path.abspath(pfy_resolved)}
        main_text = _read_text_file(pfy_resolved)
        user_text, user_sources = _expand_includes_from_text(
            main_text, base_dir, visited, os.path.abspath(pfy_resolved)
        )
        
        # Merge task sources
        combined_sources = {}
        combined_sources.update(always_available_sources)
        combined_sources.update(user_sources)
        
        # Combine texts: always-available first, then user's tasks
        combined_text = always_available_text + "\n\n" + user_text
        return combined_text, combined_sources
    
    # No Pfyfile found
    # If user explicitly specified a file that doesn't exist, raise an error
    if file_arg and not os.path.exists(pfy_resolved):
        raise FileNotFoundError(f"Specified Pfyfile not found: {file_arg}")

    # When running without a project Pfyfile, keep root tied to invocation cwd so
    # built-ins remain predictable.
    _config.PFY_ROOT = os.getcwd()
    _sync_config_globals()
    os.environ.setdefault("PFY_ROOT", _config.PFY_ROOT)
    
    # Otherwise, return always-available tasks only (or PFY_EMBED if that doesn't exist)
    if always_available_text:
        return always_available_text, always_available_sources
    return PFY_EMBED, {}


def _normalize_hosts(hosts_list: List[str]) -> List[str]:
    """Normalize a list of host specifications."""
    normalized = []
    for h in hosts_list:
        if h and h not in normalized:
            normalized.append(h)
    return normalized


def _merge_env_hosts(env_names: List[str]) -> List[str]:
    """Merge hosts from environment variables."""
    hosts = []
    for env_name in env_names:
        if env_name in ENV_MAP:
            env_hosts = ENV_MAP[env_name]
            if isinstance(env_hosts, list):
                hosts.extend(env_hosts)
            elif isinstance(env_hosts, str):
                hosts.append(env_hosts)
    return hosts


def _dedupe_preserve_order(items: List[str]) -> List[str]:
    """Remove duplicates while preserving order."""
    seen = set()
    result = []
    for item in items:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result


def _parse_host(
    host_spec: str,
    default_user: Optional[str] = None,
    default_port: Optional[int] = None
) -> Dict[str, Any]:
    """Parse a host specification into components."""
    # Handle @local
    if host_spec == "@local":
        return {"host": "localhost", "user": None, "port": None, "local": True}
    
    # Parse user@host:port format
    user = default_user
    host = host_spec
    port = default_port
    
    if "@" in host_spec:
        user, host = host_spec.split("@", 1)
    
    if ":" in host:
        host, port_str = host.rsplit(":", 1)
        try:
            port = int(port_str)
        except ValueError:
            pass
    
    return {
        "host": host,
        "user": user,
        "port": port,
        "local": False
    }


def _c_for(
    host_spec: Dict[str, Any],
    sudo: bool = False,
    sudo_user: Optional[str] = None
) -> Tuple[Optional[Connection], Dict[str, Any]]:
    """Create a Fabric connection for a host specification."""
    if host_spec.get("local"):
        return None, host_spec
    
    connect_kwargs = {}
    if host_spec.get("port"):
        connect_kwargs["port"] = host_spec["port"]
    
    conn = Connection(
        host=host_spec["host"],
        user=host_spec.get("user"),
        connect_kwargs=connect_kwargs
    )
    
    return conn, host_spec


def _exec_line_fabric(
    ln: str,
    connection: Optional[Connection],
    env_vars: Dict[str, str],
    task_name: str,
    sudo: bool = False,
    sudo_user: Optional[str] = None,
    cwd: Optional[str] = None,
) -> int:
    """Execute a line using Fabric."""
    if connection is None:
        # Local execution
        import subprocess
        try:
            result = subprocess.run(
                ln,
                shell=True,
                env={**os.environ, **env_vars},
                capture_output=False,
                cwd=cwd,
            )
            return result.returncode
        except Exception as e:
            print(f"Error executing command: {e}", file=sys.stderr)
            return 1
    else:
        # Remote execution via Fabric
        try:
            kwargs = {"env": env_vars}
            if sudo:
                kwargs["user"] = sudo_user
                result = connection.sudo(ln, **kwargs)
            else:
                result = connection.run(ln, **kwargs)
            return 0 if result.ok else result.return_code
        except Exception as e:
            print(f"Error executing remote command: {e}", file=sys.stderr)
            return 1


def list_dsl_tasks_with_desc(file_arg: Optional[str] = None) -> List[Tuple[str, Optional[str], List[str]]]:
    """List all tasks with their descriptions and aliases."""
    try:
        dsl_src, task_sources = _load_pfy_source_with_includes(file_arg=file_arg)
        dsl_tasks = parse_pfyfile_text(dsl_src, task_sources)
        result = []
        for name, task in sorted(dsl_tasks.items()):
            result.append((name, task.description, task.aliases))
        return result
    except FileNotFoundError as e:
        # Re-raise file not found errors so they can be handled appropriately
        raise
    except Exception as e:
        # Log the error and re-raise so callers know what went wrong
        import sys
        print(f"Error loading tasks: {e}", file=sys.stderr)
        raise


def _print_list(file_arg: Optional[str] = None) -> None:
    """Print a user-oriented list of available tasks."""
    tasks = list_dsl_tasks_with_desc(file_arg=file_arg)

    print("Built-ins:")
    if BUILTINS:
        print("  " + "  ".join(sorted(BUILTINS.keys())))
    else:
        print("  <none>")

    if not tasks:
        return

    grouped: Dict[str, List[Tuple[str, Optional[str], List[str]]]] = {}
    for name, desc, aliases in tasks:
        prefix = name.split("-", 1)[0] if "-" in name else "core"
        grouped.setdefault(prefix, []).append((name, desc, aliases))

    for prefix in sorted(grouped.keys()):
        print(f"\n[{prefix}]")
        for name, desc, aliases in sorted(grouped[prefix], key=lambda item: item[0]):
            alias_text = f" (aliases: {', '.join(aliases)})" if aliases else ""
            desc_text = f" — {desc}" if desc else ""
            print(f"  {name}{desc_text}{alias_text}")


def _print_task_help(task_name: str, file_arg: Optional[str] = None) -> int:
    """Print a detailed help menu for the named task."""
    try:
        dsl_src, task_sources = _load_pfy_source_with_includes(file_arg=file_arg)
        dsl_tasks = parse_pfyfile_text(dsl_src, task_sources)
    except FileNotFoundError as exc:
        print(f"Error loading Pfyfile: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"Error loading Pfyfile: {exc}", file=sys.stderr)
        return 1

    task = dsl_tasks.get(task_name)
    if task is None:
        builtin_lines = BUILTINS.get(task_name)
        if builtin_lines:
            print(f"Built-in task: {task_name}")
            for line in builtin_lines:
                print(f"  {line.rstrip()}" if line.rstrip() else "  <empty line>")
            return 0
        print(f"Task '{task_name}' not found.", file=sys.stderr)
        return 1

    def _print_section(title: str, entries: List[str]) -> None:
        if not entries:
            return
        print(f"\n{title}:")
        for entry in entries:
            print(f"  {entry}")

    print(f"Task: {task.name}")
    if task.aliases:
        print(f"Aliases: {', '.join(task.aliases)}")
    if task.category:
        print(f"Category: {task.category}")
    if task.source_file:
        print(f"Defined in: {task.source_file}")
    usage = task.synopsis or f"pf {task.name}"
    print(f"\nUsage: {usage}")
    if task.description:
        print(f"\nDescription: {task.description}")

    if task.params:
        print("\nParameter defaults:")
        for key, value in task.params.items():
            display = value if value else "(unset)"
            print(f"  {key} = {display}")

    _print_section("Examples", task.examples)
    _print_section("Prerequisites", task.prerequisites)
    _print_section("Troubleshooting", task.troubleshooting)
    _print_section("See also", task.see_also)
    _print_section("Use cases", task.use_cases)
    _print_section("Notes", task.notes)
    if task.tags:
        _print_section("Tags", [", ".join(task.tags)])

    if task.lines:
        print("\nTask body:")
        for line in task.lines:
            print(f"  {line.rstrip()}")

    return 0


def run_task_by_name(
    task_name: str,
    file_arg: Optional[str] = None,
    hosts_arg: Optional[str] = None,
    env_arg: Optional[List[str]] = None,
    dry_run: bool = False,
    debug: bool = False,
    parallel: bool = False,
    task_args: Optional[List[str]] = None,
) -> int:
    """
    Minimal task runner used by refactored CLI modules.

    Current implementation executes tasks locally and supports
    env/shell lines; other verbs are skipped with a notice.
    """
    try:
        dsl_src, task_sources = _load_pfy_source_with_includes(file_arg=file_arg)
        dsl_tasks = parse_pfyfile_text(dsl_src, task_sources)
    except Exception as e:
        print(f"Error loading Pfyfile: {e}", file=sys.stderr)
        return 1

    if task_name not in dsl_tasks:
        print(f"Task '{task_name}' not found.", file=sys.stderr)
        return 1

    lines = dsl_tasks[task_name].lines
    task_env: Dict[str, str] = {}
    params = {}

    rc = 0
    shell_lang: Optional[str] = None
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("env "):
            for tok in shlex.split(stripped)[1:]:
                if "=" in tok:
                    k, v = tok.split("=", 1)
                    task_env[k] = _interpolate(v, params, task_env)
            continue

        if stripped == "shell_lang" or stripped.startswith("shell_lang "):
            lang = stripped[len("shell_lang") :].strip()
            if not lang or lang.lower() in {"default", "none"}:
                shell_lang = None
            else:
                shell_lang = lang
            continue

        if not stripped.startswith("shell "):
            print(f"[skip] unsupported verb in task '{task_name}': {stripped}", file=sys.stderr)
            continue

        shell_cmd = stripped[6:].strip()

        shell_cmd = _interpolate(shell_cmd, params, task_env)

        lang_hint = shell_lang
        m = _LANG_BRACKET_RE.match(shell_cmd)
        if m:
            lang_hint = m.group(1).strip()
            shell_cmd = m.group(2)

        output_path = None
        if lang_hint:
            heredoc = _extract_polyglot_heredoc(shell_cmd)
            if heredoc:
                shell_cmd, output_path = heredoc

            rendered, _ = _render_polyglot_command(lang_hint, shell_cmd, None)
            if rendered:
                shell_cmd = rendered

            if output_path:
                shell_cmd = f"(\n{shell_cmd}\n) > {shlex.quote(output_path)}"

        rc = _exec_line_fabric(shell_cmd, None, task_env, task_name, False, None)
        if rc != 0:
            print(f"Command failed with exit code {rc}: {stripped}", file=sys.stderr)
            return rc

    return rc


def get_alias_map(file_arg: Optional[str] = None) -> Dict[str, str]:
    """Get mapping of aliases to task names."""
    try:
        dsl_src, task_sources = _load_pfy_source_with_includes(file_arg=file_arg)
        dsl_tasks = parse_pfyfile_text(dsl_src, task_sources)
        alias_map = {}
        for name, task in dsl_tasks.items():
            for alias in task.aliases:
                alias_map[alias] = name
        return alias_map
    except FileNotFoundError:
        # If file doesn't exist, just return empty map (this is expected in some cases)
        return {}
    except Exception:
        # For other errors, return empty map but this shouldn't normally happen
        return {}


def _alias_map(names: List[str]) -> Dict[str, str]:
    """Build a normalized alias map for task names."""
    amap: Dict[str, str] = {}
    for name in names:
        if not name:
            continue
        amap[name] = name
        amap[name.replace("_", "-")] = name
        amap[name.replace("-", "_")] = name
        amap[name.replace("-", " ")] = name
        amap[name.replace("_", " ")] = name
    return amap


def main(argv: List[str]) -> int:
    """Main entry point for pf command-line interface.
    
    Args:
        argv: Command-line arguments (excluding program name)
    
    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    # Handle debug-off command
    tasks = argv
    if not tasks:
        tasks = ["list"]
    
    pfy_file_arg = None
    env_names: List[str] = []
    host_specs: List[str] = []
    user: Optional[str] = None
    port: Optional[int] = None
    sudo = False
    sudo_user: Optional[str] = None

    filtered: List[str] = []
    i = 0
    while i < len(tasks):
        arg = tasks[i]

        if arg.endswith(".pf") and os.path.exists(arg) and pfy_file_arg is None:
            pfy_file_arg = arg
            i += 1
            continue

        if arg.startswith("env="):
            env_names.append(arg.split("=", 1)[1])
            i += 1
            continue
        if arg.startswith("--env="):
            env_names.append(arg.split("=", 1)[1])
            i += 1
            continue
        if arg == "--env" and i + 1 < len(tasks):
            env_names.append(tasks[i + 1])
            i += 2
            continue

        if arg.startswith("hosts="):
            host_specs.extend(_normalize_hosts(arg.split("=", 1)[1]))
            i += 1
            continue
        if arg.startswith("--hosts="):
            host_specs.extend(_normalize_hosts(arg.split("=", 1)[1]))
            i += 1
            continue
        if arg == "--hosts" and i + 1 < len(tasks):
            host_specs.extend(_normalize_hosts(tasks[i + 1]))
            i += 2
            continue

        if arg.startswith("host="):
            host_specs.append(arg.split("=", 1)[1])
            i += 1
            continue
        if arg.startswith("--host="):
            host_specs.append(arg.split("=", 1)[1])
            i += 1
            continue
        if arg == "--host" and i + 1 < len(tasks):
            host_specs.append(tasks[i + 1])
            i += 2
            continue

        if arg.startswith("user="):
            user = arg.split("=", 1)[1]
            i += 1
            continue
        if arg.startswith("--user="):
            user = arg.split("=", 1)[1]
            i += 1
            continue
        if arg == "--user" and i + 1 < len(tasks):
            user = tasks[i + 1]
            i += 2
            continue

        if arg.startswith("port="):
            try:
                port = int(arg.split("=", 1)[1])
            except ValueError:
                port = None
            i += 1
            continue
        if arg.startswith("--port="):
            try:
                port = int(arg.split("=", 1)[1])
            except ValueError:
                port = None
            i += 1
            continue
        if arg == "--port" and i + 1 < len(tasks):
            try:
                port = int(tasks[i + 1])
            except ValueError:
                port = None
            i += 2
            continue

        if arg in ("--sudo", "sudo=true", "sudo=1", "sudo=yes", "sudo=on"):
            sudo = True
            i += 1
            continue

        if arg.startswith("sudo_user="):
            sudo_user = arg.split("=", 1)[1]
            i += 1
            continue
        if arg.startswith("sudo-user="):
            sudo_user = arg.split("=", 1)[1]
            i += 1
            continue
        if arg.startswith("--sudo-user="):
            sudo_user = arg.split("=", 1)[1]
            i += 1
            continue
        if arg == "--sudo-user" and i + 1 < len(tasks):
            sudo_user = tasks[i + 1]
            i += 2
            continue

        filtered.append(arg)
        i += 1

    tasks = filtered

    if tasks[0] in ("list", "--list"):
        _print_list(file_arg=pfy_file_arg)
        return 0

    if tasks[0] == "help":
        if len(tasks) > 1:
            return _print_task_help(tasks[1], file_arg=pfy_file_arg)
        print(
            "Usage: pf [<pfy_file>] [env=NAME|--env=NAME|--env NAME]* [hosts=..|--hosts=..|--hosts ..] [user=..|--user=..|--user ..] [port=..|--port=..|--port ..] [sudo=true|--sudo] [sudo_user=..|--sudo-user=..|--sudo-user ..] <task|list|help> [more_tasks...]"
        )
        _print_list(file_arg=pfy_file_arg)
        return 0

    if tasks[0] in HELP_VARIATIONS:
        if len(tasks) > 1:
            return _print_task_help(tasks[1], file_arg=pfy_file_arg)
        print(
            "Usage: pf [<pfy_file>] [env=NAME|--env=NAME|--env NAME]* [hosts=..|--hosts=..|--hosts ..] [user=..|--user=..|--user ..] [port=..|--port=..|--port ..] [sudo=true|--sudo] [sudo_user=..|--sudo-user=..|--sudo-user ..] <task|list|help> [more_tasks...]"
        )
        _print_list(file_arg=pfy_file_arg)
        return 0
    
    if tasks[0] == "debug-off":
        try:
            from pf_prune import set_debug_mode

            set_debug_mode(False)
            return 0
        except PermissionError as e:
            print(f"Error: {e}", file=sys.stderr)
            return 1
        except Exception as e:
            print(f"Error disabling debug mode: {e}", file=sys.stderr)
            return 1

    # Handle prune command
    if tasks[0] == "prune":
        from pf_prune import prune_tasks

        # Parse prune-specific arguments
        dry_run = True
        verbose = False
        output_file = "pfail.fail.pf"
        prune_args = tasks[1:]
        for arg in prune_args:
            if arg in ("-d", "--dry-run"):
                dry_run = True
            elif arg in ("-v", "--verbose"):
                verbose = True
            elif arg.startswith("-o=") or arg.startswith("--output="):
                output_file = arg.split("=", 1)[1]
        passed, failed, failed_tasks = prune_tasks(
            file_arg=pfy_file_arg,
            dry_run=dry_run,
            verbose=verbose,
            output_file=output_file,
        )
        return 0 if failed == 0 else 1

    # Handle debug-on command
    if tasks[0] == "debug-on":
        try:
            from pf_prune import set_debug_mode

            set_debug_mode(True)
            return 0
        except PermissionError as e:
            print(f"Error: {e}", file=sys.stderr)
            return 1
        except Exception as e:
            print(f"Error enabling debug mode: {e}", file=sys.stderr)
            return 1

    # Handle debug-off command
    if tasks[0] == "debug-off":
        try:
            from pf_prune import set_debug_mode

            set_debug_mode(False)
            return 0
        except PermissionError as e:
            print(f"Error: {e}", file=sys.stderr)
            return 1
        except Exception as e:
            print(f"Error disabling debug mode: {e}", file=sys.stderr)
            return 1

    # Resolve hosts
    env_hosts = _merge_env_hosts(env_names)
    merged_hosts = _dedupe_preserve_order(env_hosts + host_specs)
    if not merged_hosts:
        merged_hosts = ["@local"]

    # Load tasks once
    dsl_src, task_sources = _load_pfy_source_with_includes(file_arg=pfy_file_arg)
    dsl_tasks = parse_pfyfile_text(dsl_src, task_sources)
    valid_task_names = (
        set(BUILTINS.keys())
        | set(dsl_tasks.keys())
        | {"list", "help", "--help", "--list", "prune", "debug-on", "debug-off"}
        | HELP_VARIATIONS
    )

    # Build user-defined alias map from task definitions
    user_alias_map: Dict[str, str] = {}
    for task_name, task_obj in dsl_tasks.items():
        for alias in task_obj.aliases:
            user_alias_map[alias] = task_name

    # Add user-defined aliases to valid task names for resolution
    all_valid_names = valid_task_names | set(user_alias_map.keys())

    # Parse multi-task + params: <task> [k=v ...] <task2> [k=v ...] ...
    selected = []
    j = 0
    all_names_for_alias = (
        list(BUILTINS.keys())
        + list(dsl_tasks.keys())
        + ["list", "help", "--help", "--list", "prune", "debug-on", "debug-off"]
        + list(HELP_VARIATIONS)
    )
    aliasmap_all = _alias_map(all_names_for_alias)
    # Merge user-defined aliases (take priority over normalized aliases)
    aliasmap_all.update(user_alias_map)
    while j < len(tasks):
        tname = tasks[j]

        # If this is a help variation, show help for the previous task or general help
        if tname in HELP_VARIATIONS:
            if selected:
                # Show help for the last selected task
                return _print_task_help(selected[-1][0], file_arg=pfy_file_arg)
            else:
                # Show general help
                print(
                    "Usage: pf [<pfy_file>] [env=NAME|--env=NAME|--env NAME]* [hosts=..|--hosts=..|--hosts ..] [user=..|--user=..|--user ..] [port=..|--port=..|--port ..] [sudo=true|--sudo] [sudo_user=..|--sudo-user=..|--sudo-user ..] <task|list|help> [more_tasks...]"
                )
                print("\nAvailable tasks:")
                _print_list(file_arg=pfy_file_arg)
            return 0

        if tname not in valid_task_names:
            if tname in aliasmap_all:
                tname = aliasmap_all[tname]
            else:
                import difflib as _difflib

                close = _difflib.get_close_matches(
                    tname, list(all_valid_names), n=3, cutoff=0.5
                )
                print(
                    f"[error] no such task: {tname}"
                    + (f" — did you mean: {', '.join(close)}?" if close else ""),
                    file=sys.stderr,
                )
                return 1
        j += 1
        params = {}

        def _is_valid_parameter_value(idx: int) -> bool:
            """Check if the argument at idx is a valid parameter value (not a task or another flag)."""
            if idx >= len(tasks):
                return False
            next_arg = tasks[idx]
            # Value shouldn't start with -- (another flag) or be a task name/alias
            return not next_arg.startswith("--") and next_arg not in all_valid_names

        while j < len(tasks):
            arg = tasks[j]
            # Check if this looks like the next task name (including aliases)
            if not arg.startswith("--") and "=" not in arg and arg in all_valid_names:
                break

            # Support multiple parameter formats:
            # 1. --param=value
            # 2. --param value
            # 3. param=value
            # 4. -k value (short form)
            if arg.startswith("--"):
                if "=" in arg:
                    # Format: --param=value
                    k, v = arg[2:].split("=", 1)  # Strip -- prefix
                    params[k] = v
                    j += 1
                elif _is_valid_parameter_value(j + 1):
                    # Format: --param value (next arg is the value)
                    k = arg[2:]  # Strip -- prefix
                    v = tasks[j + 1]
                    params[k] = v
                    j += 2
                else:
                    # --param without a value, or next arg is a task
                    break
            elif arg.startswith("-") and len(arg) == 2:
                # Format: -k value (short form, single letter key)
                if _is_valid_parameter_value(j + 1):
                    k = arg[1:]  # Strip - prefix
                    v = tasks[j + 1]
                    params[k] = v
                    j += 2
                else:
                    # -k without a value, or next arg is a task
                    break
            elif "=" in arg:
                # Format: param=value
                k, v = arg.split("=", 1)
                params[k] = v
                j += 1
            else:
                # Not a parameter, stop parsing params
                break
        if tname in BUILTINS:
            lines = BUILTINS[tname]
            # Builtins don't have default parameters
        else:
            task_obj = dsl_tasks[tname]
            lines = task_obj.lines
            # Start with default parameters from task definition
            merged_params = dict(task_obj.params)
            # Override with provided parameters
            merged_params.update(params)
            params = merged_params

        selected.append((tname, lines, params))

    # Execute in parallel across hosts
    def run_host(hspec: str):
        spec = _parse_host(hspec, default_user=user, default_port=port)
        prefix = f"[{hspec}]"
        if spec.get("local"):
            ctuple = (None, sudo, sudo_user)
        else:
            ctuple = _c_for(spec, sudo, sudo_user)
        connection, sflag, suser = (
            ctuple if isinstance(ctuple, tuple) else (None, sudo, sudo_user)
        )
        if connection is not None:
            try:
                connection.open()
            except Exception as e:
                # Wrap connection errors with context
                exc = PFConnectionError(
                    message=str(e),
                    host=hspec,
                    suggestion="Verify SSH credentials and network connectivity"
                )
                print(format_exception_for_user(exc, include_traceback=False), file=sys.stderr)
                return 1
        rc = 0
        for tname, lines, params in selected:
            print(f"{prefix} --> {tname}")
            task_env = {}
            for ln in lines:
                stripped = ln.strip()
                if stripped.startswith("env "):
                    for tok in shlex.split(stripped)[1:]:
                        if "=" in tok:
                            k, v = tok.split("=", 1)
                            task_env[k] = _interpolate(v, params, task_env)
                    continue
                try:
                    rc = _exec_line_fabric(
                        ln, connection, task_env, tname, sflag, suser
                    )
                    if rc != 0:
                        # Command failed - create detailed error
                        exc = PFExecutionError(
                            message=f"Command failed with exit code {rc}",
                            task_name=tname,
                            command=ln,
                            exit_code=rc,
                            environment=task_env,
                            suggestion="Check the command output above for details"
                        )
                        print(format_exception_for_user(exc, include_traceback=False), file=sys.stderr)
                        return rc
                except PFException as e:
                    # Let PF exceptions bubble up to outer handler for proper formatting
                    raise
                except Exception as e:
                    # Wrap unexpected errors
                    exc = PFExecutionError(
                        message=f"Unexpected error executing command: {e}",
                        task_name=tname,
                        command=ln,
                        environment=task_env
                    )
                    print(format_exception_for_user(exc, include_traceback=True), file=sys.stderr)
                    return 1
        if connection is not None:
            connection.close()
        return rc

    rc_total = 0
    with ThreadPoolExecutor(max_workers=min(32, len(merged_hosts))) as ex:
        futs = {ex.submit(run_host, h): h for h in merged_hosts}
        for fut in as_completed(futs):
            h = futs[fut]
            try:
                rc = fut.result()
            except PFException as e:
                # Show formatted error for PF exceptions
                print(format_exception_for_user(e, include_traceback=True), file=sys.stderr)
                rc = 1
            except Exception as e:
                # Wrap and show unexpected exceptions
                print(format_exception_for_user(e, include_traceback=True), file=sys.stderr)
                rc = 1
            rc_total = rc_total or rc

    return rc_total


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
