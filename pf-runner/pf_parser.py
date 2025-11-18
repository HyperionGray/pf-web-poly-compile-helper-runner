#!/home/punk/.venv/bin/python
"""
pf.py — single-file, symbol-free Fabric runner with a tiny DSL.

- Symbol-free DSL: shell, packages install/remove, service start/stop/enable/disable/restart, directory, copy
- describe: one-line task description shows in `pf list`
- include: top-level includes (outside tasks) to split stacks
- Per-task params: pf run-tls tls_cert=... tls_key=... port=9443 (use $tls_cert in DSL)
- Per-task env: inside a task, `env KEY=VAL KEY2=VAL2` applies to subsequent lines in that task
- Envs/hosts: env=prod, hosts=user@ip:port,..., repeatable host=...
- Parallel SSH across hosts with prefixed live output

Install
  pip install "fabric>=3.2,<4"

Usage
  pf list
  pf [env=prod]* [hosts=..|host=..]* [user=..] [port=..] [sudo=true] [sudo_user=..] <task> [k=v ...] [next_task [k=v ...]]...
"""

import os
import re
import sys
import shlex
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Tuple, Optional

from fabric import Connection

# ---------- CONFIG ----------
PFY_FILE = os.environ.get("PFY_FILE", "Pfyfile.pf")
ENV_MAP: Dict[str, List[str] | str] = {
    "local": ["@local"],
    "prod": ["ubuntu@10.0.0.5:22", "punk@10.4.4.4:24"],
    "staging": "staging@10.1.2.3:22,staging@10.1.2.4:22",
}

# ---------- Pfyfile discovery ----------
def _find_pfyfile(start_dir: Optional[str] = None, file_arg: Optional[str] = None) -> str:
    if file_arg:
        if os.path.isabs(file_arg):
            return file_arg
        return os.path.abspath(file_arg)

    pf_hint = os.environ.get("PFY_FILE", "Pfyfile.pf")
    if os.path.isabs(pf_hint):
        return pf_hint
    cur = os.path.abspath(start_dir or os.getcwd())
    while True:
        candidate = os.path.join(cur, pf_hint)
        if os.path.exists(candidate):
            return candidate
        parent = os.path.dirname(cur)
        if parent == cur:
            return os.path.join(os.getcwd(), pf_hint)
        cur = parent

# ---------- Interpolation ----------
_VAR_RE = re.compile(r"\$(\w+)|\$\{(\w+)\}")
def _interpolate(text: str, params: dict, extra_env: dict | None = None) -> str:
    merged = dict(os.environ)
    if extra_env:
        merged.update(extra_env)
    merged.update(params or {})
    def repl(m):
        key = m.group(1) or m.group(2)
        return str(merged.get(key, m.group(0)))
    return _VAR_RE.sub(repl, text)

# ---------- DSL (include + describe) ----------
class Task:
    def __init__(self, name: str):
        self.name = name
        self.lines: List[str] = []
        self.description: Optional[str] = None
    def add(self, line: str): self.lines.append(line)

def _read_text_file(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def _expand_includes_from_text(text: str, base_dir: str, visited: set[str]) -> str:
    out_lines: List[str] = []
    inside_task = False
    for raw in text.splitlines():
        line = raw.rstrip("\n")
        stripped = line.strip()
        if stripped.startswith("task "):
            inside_task = True
            out_lines.append(line); continue
        if stripped == "end":
            inside_task = False
            out_lines.append(line); continue
        if not inside_task and stripped.startswith("include "):
            try:
                toks = shlex.split(stripped)
            except ValueError:
                toks = stripped.split()
            if len(toks) >= 2:
                inc_path = toks[1]
                inc_full = inc_path if os.path.isabs(inc_path) else os.path.join(base_dir, inc_path)
                inc_full = os.path.normpath(inc_full)
                if inc_full in visited:
                    continue
                if not os.path.exists(inc_full):
                    print(f"[warn] include file not found: {inc_full}", file=sys.stderr)
                    continue
                visited.add(inc_full)
                inc_text = _read_text_file(inc_full)
                inc_expanded = _expand_includes_from_text(inc_text, os.path.dirname(inc_full), visited)
                out_lines.append(f"# --- begin include: {inc_full} ---")
                out_lines.append(inc_expanded)
                out_lines.append(f"# --- end include: {inc_full} ---")
                continue
        out_lines.append(line)
    return "\n".join(out_lines) + ("\n" if out_lines and not out_lines[-1].endswith("\n") else "")

def _load_pfy_source_with_includes(file_arg: Optional[str] = None) -> str:
    pfy_resolved = _find_pfyfile(file_arg=file_arg)
    if os.path.exists(pfy_resolved):
        base_dir = os.path.dirname(os.path.abspath(pfy_resolved)) or "."
        visited: set[str] = {os.path.abspath(pfy_resolved)}
        main_text = _read_text_file(pfy_resolved)
        return _expand_includes_from_text(main_text, base_dir, visited)
    return PFY_EMBED

def parse_pfyfile_text(text: str) -> Dict[str, Task]:
    tasks: Dict[str, Task] = {}
    cur: Optional[Task] = None
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"): continue
        if line.startswith("task "):
            name = line.split(None, 1)[1].strip()
            if not name: raise ValueError("Task name missing.")
            cur = Task(name); tasks[name] = cur; continue
        if line == "end":
            cur = None; continue
        if cur is None: continue
        if line.startswith("describe "):
            if cur.description is None:
                cur.description = line.split(None, 1)[1].strip()
            continue
        cur.add(line)
    return tasks

def list_dsl_tasks_with_desc(file_arg: Optional[str] = None) -> List[Tuple[str, Optional[str]]]:
    src = _load_pfy_source_with_includes(file_arg=file_arg)
    tasks = parse_pfyfile_text(src)
    return [(t.name, t.description) for t in tasks.values()]

# ---------- Embedded sample ----------
PFY_EMBED = r"""
task include_demo
  describe Shows that this file is active even without Pfyfile.pf
  shell echo "Include demo task ran."
end
"""

# ---------- Hosts parsing ----------
def _normalize_hosts(spec) -> List[str]:
    if spec is None: return []
    if isinstance(spec, list):
        out: List[str] = []
        for s in spec:
            if isinstance(s, list):
                out.extend(_normalize_hosts(s))
            else:
                out.extend([t.strip() for t in str(s).split(",") if t.strip()])
        return out
    return [t.strip() for t in str(spec).split(",") if t.strip()]

def _merge_env_hosts(env_names: List[str]) -> List[str]:
    merged: List[str] = []
    for name in env_names:
        if name not in ENV_MAP:
            print(f"[warn] env '{name}' not in ENV_MAP, skipping.", file=sys.stderr)
            continue
        merged.extend(_normalize_hosts(ENV_MAP[name]))
    return merged

def _dedupe_preserve_order(items: List[str]) -> List[str]:
    seen = set(); out = []
    for it in items:
        if it not in seen: seen.add(it); out.append(it)
    return out

# ---------- Executors (Fabric) ----------
def _split_kv(args: List[str]):
    pos, kv = [], {}
    for a in args:
        if "=" in a:
            k, v = a.split("=", 1)
            kv[k] = v
        else:
            pos.append(a)
    return pos, kv

def _parse_host(h: str, default_user: Optional[str], default_port: Optional[str]):
    if h == "@local": return {"local": True}
    user = default_user; port = default_port; host = h
    if "@" in host: user, host = host.split("@", 1)
    if ":" in host: host, port = host.split(":", 1)
    return {"local": False, "user": user, "host": host, "port": int(port) if port else None}

def _c_for(spec, sudo: bool, sudo_user: Optional[str]):
    if spec.get("local"): return None
    return Connection(host=spec["host"], user=spec["user"],
                      port=spec["port"] if spec["port"] else 22), sudo, sudo_user

def _run_local(cmd: str, env=None):
    import subprocess
    p = subprocess.Popen(cmd, shell=True, env=env)
    return p.wait()

def _sudo_wrap(cmd: str, sudo_user: Optional[str]) -> str:
    if sudo_user:
        return f"sudo -u {shlex.quote(sudo_user)} -H bash -lc {shlex.quote(cmd)}"
    return f"sudo bash -lc {shlex.quote(cmd)}"

def _exec_line_fabric(c: Optional[Connection], line: str, sudo: bool, sudo_user: Optional[str], prefix: str, params: dict, task_env: dict):
    # interpolate & parse
    line = _interpolate(line, params, task_env)
    parts = shlex.split(line)
    if not parts: return 0

    def run(cmd: str):
        # Build environment for this command
        merged_env = dict(os.environ)
        if task_env:
            merged_env.update({k: _interpolate(str(v), params, task_env) for k, v in task_env.items()})
        # For remote, prefix with export; for local, pass env to subprocess
        if c is None:
            full = cmd if not sudo else _sudo_wrap(cmd, sudo_user)
            # Prepend exports for display only
            if task_env:
                exports = " ".join([f"{k}={shlex.quote(str(v))}" for k,v in task_env.items()])
                display = f"{exports} {full}" if exports else full
            else:
                display = full
            print(f"{prefix}$ {display}")
            return _run_local(full, env=merged_env)
        else:
            exports = " ".join([f"export {k}={shlex.quote(str(v))};" for k,v in (task_env or {}).items()])
            shown = f"{exports} {cmd}".strip()
            print(f"{prefix}$ {(('(sudo) ' + shown) if sudo else shown)}")
            full_cmd = f"{exports} {cmd}" if exports else cmd
            if sudo:
                if sudo_user:
                    full_cmd = f"sudo -u {shlex.quote(sudo_user)} -H bash -lc {shlex.quote(full_cmd)}"
                else:
                    full_cmd = f"sudo bash -lc {shlex.quote(full_cmd)}"
            r = c.run(full_cmd, pty=True, warn=True, hide=False)
            return r.exited

    op = parts[0]; args = parts[1:]

    if op == "shell":
        cmd = " ".join(args)
        if not cmd: raise ValueError("shell needs a command")
        return run(cmd)

    if op == "packages":
        if len(args) < 2: raise ValueError("packages install/remove <names...>")
        action, names = args[0], args[1:]
        if action == "install":
            return run(" ".join(["apt -y install"] + names))
        if action == "remove":
            return run(" ".join(["apt -y remove"] + names))
        raise ValueError(f"Unknown packages action: {action}")

    if op == "service":
        if len(args) < 2: raise ValueError("service <start|stop|enable|disable|restart> <name>")
        action, name = args[0], args[1]
        map_cmd = {
            "start":   f"systemctl start {shlex.quote(name)}",
            "stop":    f"systemctl stop {shlex.quote(name)}",
            "enable":  f"systemctl enable {shlex.quote(name)}",
            "disable": f"systemctl disable {shlex.quote(name)}",
            "restart": f"systemctl restart {shlex.quote(name)}",
        }
        if action not in map_cmd: raise ValueError(f"Unknown service action: {action}")
        return run(map_cmd[action])

    if op == "directory":
        pos, kv = _split_kv(args)
        if not pos: raise ValueError("directory <path> [mode=0755]")
        path = pos[0]; mode = kv.get("mode")
        rc = run(f"mkdir -p {shlex.quote(path)}")
        if rc == 0 and mode: rc = run(f"chmod {shlex.quote(mode)} {shlex.quote(path)}")
        return rc

    if op == "copy":
        pos, kv = _split_kv(args)
        if len(pos) < 2: raise ValueError("copy <local> <remote> [mode=0644] [user=...] [group=...]")
        local, remote = pos[0], pos[1]
        mode = kv.get("mode"); owner = kv.get("user"); group = kv.get("group")
        if c is None:
            import shutil
            os.makedirs(os.path.dirname(remote), exist_ok=True)
            shutil.copyfile(local, remote)
            if mode: run(f"chmod {shlex.quote(mode)} {shlex.quote(remote)}")
            if owner or group:
                og = f"{owner or ''}:{group or ''}"
                run(f"chown {og} {shlex.quote(remote)}")
            return 0
        else:
            c.put(local, remote=remote)
            if mode: run(f"chmod {shlex.quote(mode)} {shlex.quote(remote)}")
            if owner or group:
                og = f"{owner or ''}:{group or ''}"
                run(f"chown {og} {shlex.quote(remote)}")
            return 0

    if op == "describe":
        return 0

    # 'env' is handled in the runner loop (stateful), so treat as no-op here
    if op == "env":
        return 0

    raise ValueError(f"Unknown verb: {op}")

# ---------- Built-ins ----------
BUILTINS: Dict[str, List[str]] = {
    "update": ["shell ./scripts/system-setup.sh update"],
    "upgrade": ["shell ./scripts/system-setup.sh upgrade"],
    "install-base": ["shell ./scripts/system-setup.sh install-base"],
    "setup-venv": ["shell ./scripts/system-setup.sh setup-venv"],
    "reboot": ["shell sudo shutdown -r +1 'pf reboot requested'"],
    "podman_install": [
        "packages install podman",
        "shell sudo usermod -aG podman ${SUDO_USER:-$USER} || true",
        "shell systemctl --user enable podman.socket || true",
    ],
    "docker_compat": [
        "packages install podman-docker",
        "shell sudo touch /etc/containers/nodocker",
    ],
    "nginx_install": [
        "packages install nginx",
        "service enable nginx",
        "service start nginx",
    ],
}

# ---------- CLI ----------
def _print_list(file_arg: Optional[str] = None):
    print("Built-ins:")
    print("  " + "  ".join(BUILTINS.keys()))
    dsl = list_dsl_tasks_with_desc(file_arg=file_arg)
    if dsl:
        resolved = _find_pfyfile(file_arg=file_arg)
        source = resolved if os.path.exists(resolved) else "embedded PFY_EMBED"
        print(f"From {source}:")
        for name, desc in dsl:
            if desc:
                print(f"  {name}  —  {desc}")
            else:
                print(f"  {name}")
    if ENV_MAP:
        print("Environments:")
        for k, v in ENV_MAP.items():
            vs = _normalize_hosts(v)
            print(f"  {k}: {', '.join(vs) if vs else '(empty)'}")

def _alias_map(names: List[str]) -> Dict[str, str]:
    # Provide short aliases: hyphen/underscore stripped, only alnum kept
    def norm(s: str) -> str:
        return re.sub(r"[^a-z0-9]", "", s.lower())
    m = {}
    for n in names:
        m[n] = n
        m[norm(n)] = n
    return m

def main(argv: List[str]) -> int:
    env_names: List[str] = []
    host_specs: List[str] = []
    user = None
    port = None
    sudo = False
    sudo_user = None
    pfy_file_arg = None

    if argv and not "=" in argv[0] and (os.path.exists(argv[0]) or argv[0].endswith('.pf')):
        pfy_file_arg = argv[0]
        argv = argv[1:]

    tasks: List[str] = []
    i = 0
    while i < len(argv):
        a = argv[i]
        if "=" in a and not a.startswith("--"):
            k, v = a.split("=", 1)
            if k == "hosts": host_specs.extend(_normalize_hosts(v))
            elif k == "host": host_specs.append(v.strip())
            elif k == "env": env_names.append(v.strip())
            elif k == "user": user = v
            elif k == "port": port = v
            elif k in ("sudo", "become"): sudo = v.lower() in ("1","true","yes","on")
            elif k in ("sudo_user", "become_user"): sudo_user = v
            else:
                tasks = argv[i:]; break
            i += 1; continue
        if a == "--":
            tasks = argv[i+1:]; break
        tasks = argv[i:]; break

    if not tasks or tasks[0] in {"help", "--help", "-h"}:
        if len(tasks) > 1:
            _print_task_help(tasks[1], file_arg=pfy_file_arg)
        else:
            print("Usage: pf [<pfy_file>] [env=NAME]* [hosts=..|host=..]* [user=..] [port=..] [sudo=true] [sudo_user=..] <task|list|help> [more_tasks...]")
            print("\nAvailable tasks:")
            _print_list(file_arg=pfy_file_arg)
        return 0
    if tasks[0] == "list":
        _print_list(file_arg=pfy_file_arg); return 0

    # Resolve hosts
    env_hosts = _merge_env_hosts(env_names)
    merged_hosts = _dedupe_preserve_order(env_hosts + host_specs)
    if not merged_hosts:
        merged_hosts = ["@local"]

    # Load tasks once
    dsl_src = _load_pfy_source_with_includes(file_arg=pfy_file_arg)
    dsl_tasks = parse_pfyfile_text(dsl_src)
    valid_task_names = set(BUILTINS.keys()) | set(dsl_tasks.keys()) | {"list", "help", "--help"}

    # Parse multi-task + params: <task> [k=v ...] <task2> [k=v ...] ...
    selected = []
    j = 0
    all_names_for_alias = list(BUILTINS.keys()) + list(dsl_tasks.keys()) + ["list","help","--help"]
    aliasmap_all = _alias_map(all_names_for_alias)
    while j < len(tasks):
        tname = tasks[j]
        if tname not in valid_task_names:
            if tname in aliasmap_all:
                tname = aliasmap_all[tname]
            else:
                import difflib as _difflib
                close = _difflib.get_close_matches(tname, list(valid_task_names), n=3, cutoff=0.5)
                print(f"[error] no such task: {tname}" + (f" — did you mean: {', '.join(close)}?" if close else ""), file=sys.stderr)
                return 1
        j += 1
        params = {}
        while j < len(tasks) and ("=" in tasks[j]) and (not tasks[j].startswith("--")):
            k, v = tasks[j].split("=", 1)
            params[k] = v
            j += 1
        if tname in BUILTINS:
            lines = BUILTINS[tname]
        else:
            lines = dsl_tasks[tname].lines
        selected.append((tname, lines, params))

    # Execute in parallel across hosts
    def run_host(hspec: str):
        spec = _parse_host(hspec, default_user=user, default_port=port)
        prefix = f"[{hspec}]"
        if spec.get("local"):
            ctuple = (None, sudo, sudo_user)
        else:
            ctuple = _c_for(spec, sudo, sudo_user)
        c, sflag, suser = ctuple if isinstance(ctuple, tuple) else (None, sudo, sudo_user)
        if c is not None:
            try:
                c.open()
            except Exception as e:
                print(f"{prefix} connect error: {e}", file=sys.stderr)
                return 1
        rc = 0
        for tname, lines, params in selected:
            print(f"{prefix} --> {tname}")
            task_env = {}
            for ln in lines:
                stripped = ln.strip()
                if stripped.startswith('env '):
                    for tok in shlex.split(stripped)[1:]:
                        if '=' in tok:
                            k,v = tok.split('=',1)
                            task_env[k] = _interpolate(v, params, task_env)
                    continue
                try:
                    rc = _exec_line_fabric(c, ln, sflag, suser, prefix, params, task_env)
                    if rc != 0:
                        print(f"{prefix} !! command failed (rc={rc}): {ln}", file=sys.stderr)
                        return rc
                except Exception as e:
                    print(f"{prefix} !! error: {e}", file=sys.stderr)
                    return 1
        if c is not None:
            c.close()
        return rc

    rc_total = 0
    with ThreadPoolExecutor(max_workers=min(32, len(merged_hosts))) as ex:
        futs = {ex.submit(run_host, h): h for h in merged_hosts}
        for fut in as_completed(futs):
            h = futs[fut]
            try:
                rc = fut.result()
            except Exception as e:
                print(f"[{h}] !! unhandled: {e}", file=sys.stderr)
                rc = 1
            rc_total = rc_total or rc

    return rc_total

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
