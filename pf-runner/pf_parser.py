#!/usr/bin/env python3
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
from typing import List, Dict, Tuple, Optional, Callable

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

# ---------- Polyglot shell helpers ----------
_POLY_DELIM = "__PFY_LANG__"


def _cmd_str(parts: List[str] | Tuple[str, ...]) -> str:
    return " ".join(shlex.quote(p) for p in parts)


def _poly_args(args: List[str]) -> str:
    cleaned = [a for a in args if a]
    return " ".join(shlex.quote(a) for a in cleaned)


def _ensure_newline(src: str) -> str:
    return src if src.endswith("\n") else f"{src}\n"


def _build_script_command(interpreter_cmd: str, ext: str, code: str, args: List[str], basename: str = "pf_poly") -> str:
    code = _ensure_newline(code)
    arg_str = _poly_args(args)
    return (
        "tmpdir=$(mktemp -d)\n"
        f'src="$tmpdir/{basename}{ext}"\n'
        "cat <<'"
        + _POLY_DELIM
        + "' > \"$src\"\n"
        f"{code}"
        + _POLY_DELIM
        + "\nchmod +x \"$src\" 2>/dev/null || true\n"
        + f"{interpreter_cmd} \"$src\""
        + (f" {arg_str}" if arg_str else "")
        + "\nrc=$?\nrm -rf \"$tmpdir\"\nexit $rc\n"
    )


def _build_compile_command(
    ext: str,
    code: str,
    compiler_cmd: str,
    run_cmd: str,
    args: List[str],
    setup_lines: List[str] | None = None,
    basename: str = "pf_poly",
    append_args: bool = True,
) -> str:
    code = _ensure_newline(code)
    arg_str = _poly_args(args)
    setup = "\n".join(setup_lines or [])
    if setup:
        setup += "\n"
    mapping = {
        "src": '"$src"',
        "bin": '"$bin"',
        "dir": '"$tmpdir"',
        "classes": '"$classes"',
        "jar": '"$jar"',
    }
    compiler = compiler_cmd.format(**mapping)
    run_mapping = dict(mapping)
    run_mapping["args"] = arg_str
    runner = run_cmd.format(**run_mapping)
    if append_args and arg_str:
        runner = f"{runner} {arg_str}"
    return (
        "tmpdir=$(mktemp -d)\n"
        f'src="$tmpdir/{basename}{ext}"\n'
        'bin="$tmpdir/pf_poly_bin"\n'
        + setup
        + "cat <<'"
        + _POLY_DELIM
        + "' > \"$src\"\n"
        f"{code}"
        + _POLY_DELIM
        + "\n"
        + compiler
        + "\nrc=$?\n"
        + "if [ $rc -eq 0 ]; then\n"
        + f"  {runner}\n"
        + "  rc=$?\n"
        + "fi\n"
        + "rm -rf \"$tmpdir\"\nexit $rc\n"
    )


def _build_browser_js_command(code: str, args: List[str]) -> str:
    code = _ensure_newline(code)
    arg_str = _poly_args(args)
    snippet = textwrap.indent(code, "  ")
    body = (
        "const { chromium } = require('playwright');\n"
        "(async () => {\n"
        "  const browser = await chromium.launch({ headless: process.env.PF_HEADFUL ? false : true });\n"
        "  const page = await browser.newPage();\n"
        f"{snippet}"
        "  await browser.close();\n"
        "})().catch(err => {\n"
        "  console.error(err);\n"
        "  process.exit(1);\n"
        "});\n"
    )
    return (
        "tmpdir=$(mktemp -d)\n"
        'src="$tmpdir/pf_poly_browser.mjs"\n'
        "cat <<'"
        + _POLY_DELIM
        + "' > \"$src\"\n"
        + body
        + _POLY_DELIM
        + "\nnode \"$src\""
        + (f" {arg_str}" if arg_str else "")
        + "\nrc=$?\nrm -rf \"$tmpdir\"\nexit $rc\n"
    )


def _script_profile(parts: List[str] | Tuple[str, ...], ext: str, basename: str = "pf_poly"):
    cmd = _cmd_str(parts)

    def builder(code: str, args: List[str]) -> str:
        return _build_script_command(cmd, ext, code, args, basename=basename)

    return builder


def _compile_profile(
    ext: str,
    compiler_cmd: str,
    run_cmd: str,
    setup_lines: List[str] | None = None,
    basename: str = "pf_poly",
    append_args: bool = True,
):
    def builder(code: str, args: List[str]) -> str:
        return _build_compile_command(
            ext,
            code,
            compiler_cmd,
            run_cmd,
            args,
            setup_lines or [],
            basename=basename,
            append_args=append_args,
        )

    return builder


def _java_openjdk_builder() -> Callable[[str, List[str]], str]:
    return _compile_profile(
        ".java",
        "javac -d {classes} {src}",
        "(cd {classes} && java Main{args})",
        setup_lines=['classes="$tmpdir/classes"', 'mkdir -p "$classes"'],
        basename="Main",
        append_args=False,
    )


def _java_android_builder() -> Callable[[str, List[str]], str]:
    def builder(code: str, args: List[str]) -> str:
        code = _ensure_newline(code)
        arg_str = _poly_args(args)
        body = f"""tmpdir=$(mktemp -d)
src="$tmpdir/Main.java"
classes="$tmpdir/classes"
dexdir="$tmpdir/dex"
mkdir -p "$classes" "$dexdir"
cat <<'{_POLY_DELIM}' > "$src"
{code}{_POLY_DELIM}

ANDROID_SDK="${{ANDROID_SDK_ROOT:-${{ANDROID_HOME:-}}}}"
platform_jar="${{ANDROID_PLATFORM_JAR:-}}"
if [ -z "$platform_jar" ] && [ -n "$ANDROID_SDK" ]; then
  latest_platform=$(ls -1 "$ANDROID_SDK/platforms" 2>/dev/null | sort -V | tail -1)
  if [ -n "$latest_platform" ] && [ -f "$ANDROID_SDK/platforms/$latest_platform/android.jar" ]; then
    platform_jar="$ANDROID_SDK/platforms/$latest_platform/android.jar"
  fi
fi
javac_cp=""
if [ -n "$platform_jar" ] && [ -f "$platform_jar" ]; then
  javac_cp="-classpath $platform_jar"
fi
javac $javac_cp -d "$classes" "$src"
rc=$?
if [ $rc -ne 0 ]; then
  rm -rf "$tmpdir"
  exit $rc
fi

d8_bin="${{ANDROID_D8:-}}"
if [ -z "$d8_bin" ] && [ -n "$ANDROID_SDK" ]; then
  latest_bt=$(ls -1 "$ANDROID_SDK/build-tools" 2>/dev/null | sort -V | tail -1)
  if [ -n "$latest_bt" ] && [ -x "$ANDROID_SDK/build-tools/$latest_bt/d8" ]; then
    d8_bin="$ANDROID_SDK/build-tools/$latest_bt/d8"
  fi
fi

if [ -n "$d8_bin" ] && command -v dalvikvm >/dev/null 2>&1; then
  "$d8_bin" --output "$dexdir" "$classes" >/dev/null
  rc=$?
  if [ $rc -eq 0 ]; then
    dalvikvm -cp "$dexdir/classes.dex" Main{" " + arg_str if arg_str else ""}
    rc=$?
    rm -rf "$tmpdir"
    exit $rc
  fi
fi

(cd "$classes" && java Main{" " + arg_str if arg_str else ""})
rc=$?
rm -rf "$tmpdir"
exit $rc
"""
        return body

    return builder


POLYGLOT_LANGS: Dict[str, Callable[[str, List[str]], str]] = {
    # Shells
    "bash": _script_profile(["bash"], ".sh"),
    "sh": _script_profile(["sh"], ".sh"),
    "dash": _script_profile(["dash"], ".sh"),
    "zsh": _script_profile(["zsh"], ".sh"),
    "fish": _script_profile(["fish"], ".fish"),
    "ksh": _script_profile(["ksh"], ".sh"),
    "tcsh": _script_profile(["tcsh"], ".csh"),
    "pwsh": _script_profile(["pwsh", "-NoLogo", "-NonInteractive", "-File"], ".ps1"),

    # Scripting / Interpreted
    "python": _script_profile(["python3"], ".py"),
    "node": _script_profile(["node"], ".js"),
    "deno": _script_profile(["deno", "run"], ".ts"),
    "ts-node": _script_profile(["ts-node"], ".ts"),
    "perl": _script_profile(["perl"], ".pl"),
    "php": _script_profile(["php"], ".php"),
    "ruby": _script_profile(["ruby"], ".rb"),
    "r": _script_profile(["Rscript"], ".R"),
    "julia": _script_profile(["julia"], ".jl"),
    "haskell": _script_profile(["runghc"], ".hs"),
    "ocaml": _script_profile(["ocaml"], ".ml"),
    "elixir": _script_profile(["elixir"], ".exs"),
    "dart": _script_profile(["dart", "run"], ".dart"),
    "lua": _script_profile(["lua"], ".lua"),

    # Compiled / AOT
    "go": _script_profile(["go", "run"], ".go"),
    "rust": _compile_profile(".rs", "rustc {src} -o {bin}", "{bin}"),
    "c": _compile_profile(".c", "clang -x c {src} -o {bin}", "{bin}"),
    "cpp": _compile_profile(".cc", "clang++ {src} -o {bin}", "{bin}"),
    "c-llvm": _compile_profile(".c", "clang -x c -O3 -S -emit-llvm {src} -o {bin}.ll && cat {bin}.ll", "echo '(LLVM IR generated with O3 optimization)'"),
    "cpp-llvm": _compile_profile(".cc", "clang++ -O3 -S -emit-llvm {src} -o {bin}.ll && cat {bin}.ll", "echo '(LLVM IR generated with O3 optimization)'"),
    "c-llvm-bc": _compile_profile(".c", "clang -x c -O3 -c -emit-llvm {src} -o {bin}.bc && llvm-dis {bin}.bc -o {bin}.ll && cat {bin}.ll", "echo '(LLVM bitcode generated with O3 optimization)'"),
    "cpp-llvm-bc": _compile_profile(".cc", "clang++ -O3 -c -emit-llvm {src} -o {bin}.bc && llvm-dis {bin}.bc -o {bin}.ll && cat {bin}.ll", "echo '(LLVM bitcode generated with O3 optimization)'"),
    "fortran": _compile_profile(".f90", "gfortran {src} -o {bin}", "{bin}"),
    "fortran-llvm": _compile_profile(".f90", "flang -O3 {src} -S -emit-llvm -o {bin}.ll && cat {bin}.ll", "echo '(LLVM IR generated with O3 optimization)'"),
    "asm": _compile_profile(".s", "clang -x assembler {src} -o {bin}", "{bin}"),
    "zig": _compile_profile(".zig", "zig build-exe -O Debug -femit-bin={bin} {src}", "{bin}"),
    "nim": _compile_profile(".nim", "nim c -o:{bin} {src}", "{bin}"),
    "crystal": _compile_profile(".cr", "crystal build -o {bin} {src}", "{bin}"),
    "haskell-compile": _compile_profile(".hs", "ghc -o {bin} {src}", "{bin}"),
    "ocamlc": _compile_profile(".ml", "ocamlc -o {bin} {src}", "{bin}"),

    # Java / JVM
    "java-openjdk": _java_openjdk_builder(),
    "java-android": _java_android_builder(),
}

POLYGLOT_ALIASES = {
    # Shells
    "shell": "bash",
    "sh": "sh",
    "zshell": "zsh",
    "powershell": "pwsh",
    "ps1": "pwsh",

    # Python
    "py": "python",
    "python3": "python",
    "ipython": "python",

    # JavaScript / TypeScript
    "javascript": "node",
    "js": "node",
    "nodejs": "node",
    "ts": "deno",
    "typescript": "deno",
    "tsnode": "ts-node",

    # C-family
    "c++": "cpp",
    "cxx": "cpp",
    "clang": "c",
    "clang++": "cpp",
    "g++": "cpp",
    "gcc": "c",
    "c-ir": "c-llvm",
    "c-ll": "c-llvm",
    "cpp-ir": "cpp-llvm",
    "cpp-ll": "cpp-llvm",
    "c-bc": "c-llvm-bc",
    "cpp-bc": "cpp-llvm-bc",
    "fortran-ll": "fortran-llvm",
    "fortran-ir": "fortran-llvm",

    # Others common
    "golang": "go",
    "rb": "ruby",
    "pl": "perl",
    "ml": "ocaml",
    "hs": "haskell",
    "fortran90": "fortran",
    "gfortran": "fortran",
    "java": "java-openjdk",
    "java-openjdk": "java-openjdk",
    "java-android-google": "java-android",
    "java-android": "java-android",
    "android-java": "java-android",
    "fishshell": "fish",
    "shellscript": "bash",
    "dashshell": "dash",
    "asm86": "asm",
}


def _parse_polyglot_template(template: str) -> Optional[str]:
    stripped = template.strip()
    m = re.match(r"^(?:lang|language|polyglot)\s*(?:[:=]|\s+)\s*(.+)$", stripped, re.IGNORECASE)
    if not m:
        return None
    return m.group(1).strip().lower()


def _extract_polyglot_source(cmd: str, working_dir: Optional[str] = None) -> Tuple[str, List[str], Optional[str]]:
    raw = cmd.strip()
    base_dir = working_dir or PFY_ROOT or os.getcwd()
    if not raw:
        raise ValueError("polyglot shell requires code or @file reference")
    if raw.startswith("@") or raw.startswith("file:"):
        tokens = shlex.split(cmd)
        if not tokens:
            raise ValueError("polyglot file token missing")
        source_token = tokens.pop(0)
        if source_token.startswith("@"):
            rel_path = source_token[1:]
        else:
            rel_path = source_token[5:]
        full_path = rel_path if os.path.isabs(rel_path) else os.path.join(base_dir, rel_path)
        if not os.path.exists(full_path):
            raise FileNotFoundError(f"polyglot source file not found: {full_path}")
        with open(full_path, "r", encoding="utf-8") as poly_file:
            code = poly_file.read()
        if tokens and tokens[0] == "--":
            tokens = tokens[1:]
        return code, tokens, full_path
    return cmd, [], None


def _render_polyglot_command(lang_hint: Optional[str], cmd: str, working_dir: Optional[str]) -> Tuple[Optional[str], Optional[str]]:
    if not lang_hint:
        return None, None
    lang_key = _canonical_lang(lang_hint)
    builder = POLYGLOT_LANGS[lang_key]
    snippet, lang_args, _ = _extract_polyglot_source(cmd, working_dir)
    rendered = builder(snippet, lang_args)
    return rendered, lang_key

# ---------- DSL (include + describe) ----------
class Task:
    def __init__(self, name: str, source_file: Optional[str] = None):
        self.name = name
        self.lines: List[str] = []
        self.description: Optional[str] = None
        self.source_file = source_file  # Track which file this task came from
    def add(self, line: str): self.lines.append(line)

def _read_text_file(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def _expand_includes_from_text(text: str, base_dir: str, visited: set[str], current_file: Optional[str] = None) -> Tuple[str, Dict[str, str]]:
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
            task_name = stripped.split(None, 1)[1].strip() if len(stripped.split()) > 1 else ""
            current_task_name = task_name
            # Track the source file for this task (use current_file if in an include)
            if current_file:
                task_sources[task_name] = current_file
            out_lines.append(line); continue
        if stripped == "end":
            inside_task = False
            current_task_name = None
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
                
                # Process included file with its path as current_file
                inc_expanded, inc_sources = _expand_includes_from_text(inc_text, os.path.dirname(inc_full), visited, inc_full)
                
                # Merge task sources
                task_sources.update(inc_sources)
                
                out_lines.append(f"# --- begin include: {inc_full} ---")
                out_lines.append(inc_expanded)
                out_lines.append(f"# --- end include: {inc_full} ---")
                continue
        out_lines.append(line)
    return "\n".join(out_lines) + ("\n" if out_lines and not out_lines[-1].endswith("\n") else ""), task_sources

def _load_pfy_source_with_includes(file_arg: Optional[str] = None) -> Tuple[str, Dict[str, str]]:
    """Load Pfyfile with includes expanded, return (text, task_sources)"""
    pfy_resolved = _find_pfyfile(file_arg=file_arg)
    if os.path.exists(pfy_resolved):
        base_dir = os.path.dirname(os.path.abspath(pfy_resolved)) or "."
        visited: set[str] = {os.path.abspath(pfy_resolved)}
        main_text = _read_text_file(pfy_resolved)
        return _expand_includes_from_text(main_text, base_dir, visited)
    return PFY_EMBED, {}

def parse_pfyfile_text(text: str, task_sources: Optional[Dict[str, str]] = None) -> Dict[str, Task]:
    """Parse Pfyfile text into Task objects with optional source tracking"""
    tasks: Dict[str, Task] = {}
    cur: Optional[Task] = None
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"): continue
        if line.startswith("task "):
            name = line.split(None, 1)[1].strip()
            if not name: raise ValueError("Task name missing.")
            source_file = task_sources.get(name) if task_sources else None
            cur = Task(name, source_file=source_file)
            tasks[name] = cur
            continue
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
    src, task_sources = _load_pfy_source_with_includes(file_arg=file_arg)
    tasks = parse_pfyfile_text(src, task_sources)
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
    # Use bash explicitly for better bash syntax support (arrays, [[, etc.)
    # Wrap command to execute via bash -c
    bash_cmd = ["bash", "-c", cmd]
    p = subprocess.Popen(bash_cmd, env=env)
    return p.wait()

def _sudo_wrap(cmd: str, sudo_user: Optional[str]) -> str:
    if sudo_user:
        return f"sudo -u {shlex.quote(sudo_user)} -H bash -lc {shlex.quote(cmd)}"
    return f"sudo bash -lc {shlex.quote(cmd)}"

def _exec_line_fabric(c: Optional[Connection], line: str, sudo: bool, sudo_user: Optional[str], prefix: str, params: dict, task_env: dict):
    # interpolate & parse
    line = _interpolate(line, params, task_env)
    
    # Extract the verb (first word) to determine the operation
    # For 'shell' commands, we preserve the rest of the line as-is to maintain bash syntax
    stripped = line.strip()
    if not stripped: return 0
    
    # Split at most once to get the verb and the rest
    parts_split = stripped.split(maxsplit=1)
    verb = parts_split[0]
    rest_of_line = parts_split[1] if len(parts_split) > 1 else ""
    
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

    # Handle 'shell' command specially - preserve bash syntax
    if verb == "shell":
        if not rest_of_line: raise ValueError("shell needs a command")
        return run(rest_of_line)
    
    # For other commands, parse with shlex to handle quoted arguments
    parts = shlex.split(line)
    if not parts: return 0
    op = parts[0]; args = parts[1:]

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

    # ---------- Build System Helpers ----------
    if op == "makefile" or op == "make":
        # makefile [target...] [VAR=value...] [clean] [verbose] [jobs=N]
        pos, kv = _split_kv(args)
        make_args = []
        if kv.get("jobs"):
            make_args.append(f"-j{kv['jobs']}")
        elif kv.get("parallel") == "true":
            make_args.append("-j")
        if kv.get("verbose") == "true":
            make_args.append("V=1")
        # Add any VAR=value pairs
        for k, v in kv.items():
            if k not in {"jobs", "parallel", "verbose"}:
                make_args.append(f"{k}={shlex.quote(v)}")
        # Add targets
        make_args.extend([shlex.quote(t) for t in pos])
        cmd = "make " + " ".join(make_args) if make_args else "make"
        return run(cmd)

    if op == "cmake":
        # cmake [source_dir] [build_dir] [generator=...] [build_type=...] [options...]
        pos, kv = _split_kv(args)
        source_dir = pos[0] if pos else "."
        build_dir = kv.get("build_dir", "build")
        
        # Configure step
        configure_args = ["cmake", "-S", shlex.quote(source_dir), "-B", shlex.quote(build_dir)]
        if kv.get("generator"):
            configure_args.extend(["-G", shlex.quote(kv["generator"])])
        if kv.get("build_type"):
            configure_args.append(f"-DCMAKE_BUILD_TYPE={shlex.quote(kv['build_type'])}")
        # Add any other -D options
        for k, v in kv.items():
            if k not in {"build_dir", "generator", "build_type", "target", "jobs"}:
                configure_args.append(f"-D{k}={shlex.quote(v)}")
        
        rc = run(" ".join(configure_args))
        if rc != 0:
            return rc
        
        # Build step
        build_args = ["cmake", "--build", shlex.quote(build_dir)]
        if kv.get("jobs"):
            build_args.extend(["-j", kv["jobs"]])
        if kv.get("target"):
            build_args.extend(["--target", shlex.quote(kv["target"])])
        
        return run(" ".join(build_args))

    if op == "meson" or op == "ninja":
        # meson [source_dir] [build_dir] [options...]
        pos, kv = _split_kv(args)
        source_dir = pos[0] if pos else "."
        build_dir = kv.get("build_dir", "builddir")
        
        # Check if build directory already exists (reconfigure vs initial setup)
        check_cmd = f"test -f {shlex.quote(build_dir)}/build.ninja"
        rc_check = run(check_cmd)
        
        if rc_check != 0:
            # Initial setup
            setup_args = ["meson", "setup", shlex.quote(build_dir), shlex.quote(source_dir)]
            if kv.get("buildtype"):
                setup_args.append(f"--buildtype={shlex.quote(kv['buildtype'])}")
            for k, v in kv.items():
                if k not in {"build_dir", "buildtype", "target"}:
                    setup_args.append(f"-D{k}={shlex.quote(v)}")
            rc = run(" ".join(setup_args))
            if rc != 0:
                return rc
        
        # Compile
        compile_args = ["meson", "compile", "-C", shlex.quote(build_dir)]
        if kv.get("target"):
            compile_args.append(shlex.quote(kv["target"]))
        
        return run(" ".join(compile_args))

    if op == "cargo":
        # cargo <subcommand> [args...] [release] [features=...] [target=...]
        if not args:
            raise ValueError("cargo requires a subcommand (build, test, run, etc.)")
        pos, kv = _split_kv(args)
        subcommand = pos[0]
        cargo_args = ["cargo", subcommand]
        
        if kv.get("release") == "true":
            cargo_args.append("--release")
        if kv.get("features"):
            cargo_args.extend(["--features", shlex.quote(kv["features"])])
        if kv.get("target"):
            cargo_args.extend(["--target", shlex.quote(kv["target"])])
        if kv.get("manifest_path"):
            cargo_args.extend(["--manifest-path", shlex.quote(kv["manifest_path"])])
        
        # Add remaining positional args
        cargo_args.extend([shlex.quote(a) for a in pos[1:]])
        
        # Add remaining kv pairs as flags
        for k, v in kv.items():
            if k not in {"release", "features", "target", "manifest_path"}:
                if v == "true":
                    cargo_args.append(f"--{k}")
                else:
                    cargo_args.extend([f"--{k}", shlex.quote(v)])
        
        return run(" ".join(cargo_args))

    if op == "go_build" or op == "gobuild":
        # go_build [subcommand=build] [output=...] [tags=...] [race] [package]
        pos, kv = _split_kv(args)
        subcommand = kv.get("subcommand", "build")
        go_args = ["go", subcommand]
        
        if kv.get("output"):
            go_args.extend(["-o", shlex.quote(kv["output"])])
        if kv.get("tags"):
            go_args.extend(["-tags", shlex.quote(kv["tags"])])
        if kv.get("race") == "true":
            go_args.append("-race")
        if kv.get("ldflags"):
            go_args.extend(["-ldflags", shlex.quote(kv["ldflags"])])
        
        # Add package path if provided
        go_args.extend([shlex.quote(p) for p in pos])
        
        return run(" ".join(go_args))

    if op == "configure":
        # configure [prefix=...] [options...]
        pos, kv = _split_kv(args)
        configure_script = pos[0] if pos else "./configure"
        configure_args = [configure_script]
        
        if kv.get("prefix"):
            configure_args.append(f"--prefix={shlex.quote(kv['prefix'])}")
        
        # Add boolean flags
        for k, v in kv.items():
            if k == "prefix":
                continue
            if v == "true":
                configure_args.append(f"--enable-{k}")
            elif v == "false":
                configure_args.append(f"--disable-{k}")
            else:
                configure_args.append(f"--{k}={shlex.quote(v)}")
        
        return run(" ".join(configure_args))

    if op == "justfile" or op == "just":
        # justfile [recipe] [args...]
        just_args = ["just"]
        just_args.extend([shlex.quote(a) for a in args])
        return run(" ".join(just_args))

    if op == "build_detect" or op == "detect_build":
        # Detect build system and suggest command
        # This is informational only - prints what it finds
        detection_script = """
if [ -f Makefile ] || [ -f makefile ] || [ -f GNUmakefile ]; then
    echo "Detected: Makefile (use 'makefile' verb)"
fi
if [ -f CMakeLists.txt ]; then
    echo "Detected: CMake (use 'cmake' verb)"
fi
if [ -f meson.build ]; then
    echo "Detected: Meson (use 'meson' verb)"
fi
if [ -f Cargo.toml ]; then
    echo "Detected: Rust/Cargo (use 'cargo build' verb)"
fi
if [ -f go.mod ] || [ -f go.sum ]; then
    echo "Detected: Go module (use 'go_build' verb)"
fi
if [ -f configure ] || [ -f configure.ac ]; then
    echo "Detected: Autotools/Configure (use 'configure' verb)"
fi
if [ -f justfile ] || [ -f Justfile ]; then
    echo "Detected: Just (use 'justfile' verb)"
fi
if [ -f build.ninja ]; then
    echo "Detected: Ninja build files (use 'ninja' verb or run ninja directly)"
fi
if [ -f package.json ]; then
    echo "Detected: Node.js/npm project (package.json found)"
fi
if [ -f setup.py ] || [ -f pyproject.toml ]; then
    echo "Detected: Python project (setup.py or pyproject.toml found)"
fi
if [ -f build.gradle ] || [ -f build.gradle.kts ] || [ -f pom.xml ]; then
    echo "Detected: Java/JVM project (Gradle or Maven)"
fi
"""
        return run(detection_script)

    if op == "autobuild" or op == "auto_build":
        # Automagic builder - detects build system and runs appropriate build command
        # Supports: Cargo, Go, CMake, Meson, Make, npm, Python, Maven/Gradle, Just, Autotools
        # Optional parameters: target=<target>, jobs=<N>, release=<true/false>, dir=<path>
        
        pos, kv = _split_kv(args)
        target_dir = kv.get("dir", ".")
        jobs = kv.get("jobs", "4")
        is_release = kv.get("release", "").lower() in ("true", "yes", "1")
        custom_target = kv.get("target", "")
        
        autobuild_script = f"""
set -e
cd {shlex.quote(target_dir)}

echo "==> Automagic Builder: Detecting build system..."

# Priority order for build system detection (most specific to most general)
BUILD_SYSTEM=""

# 1. Check for Rust/Cargo (high priority - well-defined)
if [ -f Cargo.toml ]; then
    BUILD_SYSTEM="cargo"
    echo "✓ Detected: Rust/Cargo project"
fi

# 2. Check for Go module (high priority - well-defined)
if [ -z "$BUILD_SYSTEM" ] && [ -f go.mod ]; then
    BUILD_SYSTEM="go"
    echo "✓ Detected: Go module"
fi

# 3. Check for Node.js/npm (high priority for web projects)
if [ -z "$BUILD_SYSTEM" ] && [ -f package.json ]; then
    BUILD_SYSTEM="npm"
    echo "✓ Detected: Node.js/npm project"
fi

# 4. Check for Python project
if [ -z "$BUILD_SYSTEM" ] && ([ -f setup.py ] || [ -f pyproject.toml ]); then
    BUILD_SYSTEM="python"
    echo "✓ Detected: Python project"
fi

# 5. Check for Java/Maven
if [ -z "$BUILD_SYSTEM" ] && [ -f pom.xml ]; then
    BUILD_SYSTEM="maven"
    echo "✓ Detected: Maven project"
fi

# 6. Check for Java/Gradle
if [ -z "$BUILD_SYSTEM" ] && ([ -f build.gradle ] || [ -f build.gradle.kts ]); then
    BUILD_SYSTEM="gradle"
    echo "✓ Detected: Gradle project"
fi

# 7. Check for CMake (higher priority than raw Makefile)
if [ -z "$BUILD_SYSTEM" ] && [ -f CMakeLists.txt ]; then
    BUILD_SYSTEM="cmake"
    echo "✓ Detected: CMake project"
fi

# 8. Check for Meson
if [ -z "$BUILD_SYSTEM" ] && [ -f meson.build ]; then
    BUILD_SYSTEM="meson"
    echo "✓ Detected: Meson project"
fi

# 9. Check for Just
if [ -z "$BUILD_SYSTEM" ] && ([ -f justfile ] || [ -f Justfile ]); then
    BUILD_SYSTEM="just"
    echo "✓ Detected: Just build"
fi

# 10. Check for Autotools (before generic Makefile)
if [ -z "$BUILD_SYSTEM" ] && ([ -f configure ] || [ -f configure.ac ]); then
    BUILD_SYSTEM="autotools"
    echo "✓ Detected: Autotools/Configure"
fi

# 11. Check for generic Makefile (lowest priority)
if [ -z "$BUILD_SYSTEM" ] && ([ -f Makefile ] || [ -f makefile ] || [ -f GNUmakefile ]); then
    BUILD_SYSTEM="make"
    echo "✓ Detected: Makefile"
fi

# 12. Check for Ninja build files
if [ -z "$BUILD_SYSTEM" ] && [ -f build.ninja ]; then
    BUILD_SYSTEM="ninja"
    echo "✓ Detected: Ninja build"
fi

# If no build system detected, error out
if [ -z "$BUILD_SYSTEM" ]; then
    echo "✗ Error: No build system detected in $(pwd)"
    echo "Supported: Cargo.toml, go.mod, package.json, CMakeLists.txt, Makefile, meson.build, etc."
    exit 1
fi

echo "==> Building with $BUILD_SYSTEM..."

# Execute appropriate build command based on detected system
case "$BUILD_SYSTEM" in
    cargo)
        if [ "{is_release}" = "True" ]; then
            echo "Running: cargo build --release"
            cargo build --release
        else
            echo "Running: cargo build"
            cargo build
        fi
        ;;
    go)
        if [ -n "{custom_target}" ]; then
            echo "Running: go build -o {custom_target}"
            go build -o {shlex.quote(custom_target)}
        else
            echo "Running: go build"
            go build
        fi
        ;;
    npm)
        # Check for build script in package.json
        if grep -q '"build"' package.json 2>/dev/null; then
            echo "Running: npm run build"
            npm run build
        else
            echo "Running: npm install"
            npm install
        fi
        ;;
    python)
        if [ -f pyproject.toml ]; then
            echo "Running: pip install -e ."
            pip install -e .
        elif [ -f setup.py ]; then
            echo "Running: python setup.py build"
            python setup.py build
        fi
        ;;
    maven)
        echo "Running: mvn compile"
        mvn compile
        ;;
    gradle)
        if [ -x ./gradlew ]; then
            echo "Running: ./gradlew build"
            ./gradlew build
        else
            echo "Running: gradle build"
            gradle build
        fi
        ;;
    cmake)
        BUILD_DIR="build"
        BUILD_TYPE="Release"
        if [ "{is_release}" = "False" ]; then
            BUILD_TYPE="Debug"
        fi
        echo "Running: cmake -B $BUILD_DIR -DCMAKE_BUILD_TYPE=$BUILD_TYPE"
        cmake -B "$BUILD_DIR" -DCMAKE_BUILD_TYPE="$BUILD_TYPE"
        echo "Running: cmake --build $BUILD_DIR -j {jobs}"
        cmake --build "$BUILD_DIR" -j {jobs}
        ;;
    meson)
        BUILD_DIR="builddir"
        BUILDTYPE="release"
        if [ "{is_release}" = "False" ]; then
            BUILDTYPE="debug"
        fi
        if [ ! -d "$BUILD_DIR" ]; then
            echo "Running: meson setup $BUILD_DIR --buildtype=$BUILDTYPE"
            meson setup "$BUILD_DIR" --buildtype="$BUILDTYPE"
        fi
        echo "Running: meson compile -C $BUILD_DIR -j {jobs}"
        meson compile -C "$BUILD_DIR" -j {jobs}
        ;;
    make)
        TARGET="{custom_target if custom_target else 'all'}"
        echo "Running: make $TARGET -j{jobs}"
        make $TARGET -j{jobs}
        ;;
    just)
        if [ -n "{custom_target}" ]; then
            echo "Running: just {custom_target}"
            just {shlex.quote(custom_target)}
        else
            echo "Running: just"
            just
        fi
        ;;
    autotools)
        if [ ! -f config.status ]; then
            echo "Running: ./configure"
            ./configure
        fi
        echo "Running: make -j{jobs}"
        make -j{jobs}
        ;;
    ninja)
        echo "Running: ninja -j{jobs}"
        ninja -j{jobs}
        ;;
    *)
        echo "✗ Error: Unknown build system: $BUILD_SYSTEM"
        exit 1
        ;;
esac

echo "==> Build completed successfully with $BUILD_SYSTEM"
"""
        return run(autobuild_script)

    if op == "sync":
        # sync src=<path> dest=<path> [host=<host>] [user=<user>] [port=<port>]
        #      [excludes=["pattern1","pattern2"]] [exclude_file=<path>]
        #      [delete] [dry] [verbose]
        # Supports both local and remote (SSH) sync using rsync
        
        pos, kv = _split_kv(args)
        
        # Required parameters
        src = kv.get("src")
        dest = kv.get("dest")
        if not src or not dest:
            raise ValueError("sync requires src=<path> and dest=<path>")
        
        # Optional parameters
        host = kv.get("host")
        user = kv.get("user")
        port = kv.get("port")
        
        # Parse excludes array
        excludes_raw = kv.get("excludes", "")
        excludes = []
        if excludes_raw:
            # excludes comes as a string like "[*.log,*.tmp]"
            if excludes_raw.startswith("[") and excludes_raw.endswith("]"):
                # Remove brackets and split by comma
                excludes_str = excludes_raw[1:-1]
                if excludes_str:
                    excludes = [p.strip() for p in excludes_str.split(",")]
        
        exclude_file = kv.get("exclude_file")
        delete = "delete" in pos or kv.get("delete") == "true"
        dry = "dry" in pos or kv.get("dry") == "true"
        verbose = "verbose" in pos or kv.get("verbose") == "true"
        
        # Build rsync command parts
        rsync_parts = ["rsync", "-az"]
        
        # Add verbose flag
        if verbose:
            rsync_parts.append("-v")
        
        # Add dry-run flag
        if dry:
            rsync_parts.append("--dry-run")
        
        # Add delete flag (mirror destination)
        if delete:
            rsync_parts.append("--delete")
        
        # Add excludes with proper quoting
        for pattern in excludes:
            rsync_parts.append("--exclude")
            rsync_parts.append(shlex.quote(pattern))
        
        # Add exclude-from file
        if exclude_file:
            rsync_parts.append("--exclude-from")
            rsync_parts.append(shlex.quote(exclude_file))
        
        # Build source and destination paths
        # Source is always local
        src_path = shlex.quote(src)
        
        # Destination can be remote (SSH) or local
        if host:
            # Remote sync via SSH
            dest_spec = ""
            if user:
                dest_spec = f"{user}@"
            dest_spec += host
            if port:
                # Add SSH port option
                rsync_parts.append("-e")
                rsync_parts.append(shlex.quote(f"ssh -p {port}"))
            dest_spec += f":{dest}"
            dest_path = shlex.quote(dest_spec)
        else:
            # Local sync
            dest_path = shlex.quote(dest)
        
        # Complete command
        rsync_parts.extend([src_path, dest_path])
        
        # Execute rsync
        cmd = " ".join(rsync_parts)
        return run(cmd)

    raise ValueError(f"Unknown verb: {op}")

# ---------- Built-ins ----------
BUILTINS: Dict[str, List[str]] = {
    "update": ["shell ./scripts/system-setup.sh update"],
    "upgrade": ["shell ./scripts/system-setup.sh upgrade"],
    "install-base": ["shell ./scripts/system-setup.sh install-base"],
    "setup-venv": ["shell ./scripts/system-setup.sh setup-venv"],
    "reboot": ["shell sudo shutdown -r +1 'pf reboot requested'"],
    "completions": [
        "shell cd $(dirname $(readlink -f $(which pf 2>/dev/null || echo ./pf))) && make install-completions",
    ],
    "autobuild": [
        "autobuild",
    ],
    "build_detect": [
        "build_detect",
    ],
}

# ---------- CLI ----------
def _print_list(file_arg: Optional[str] = None):
    """Print available tasks grouped by source"""
    print("Built-ins:")
    print("  " + "  ".join(BUILTINS.keys()))
    
    # Load tasks with source tracking
    src_text, task_sources = _load_pfy_source_with_includes(file_arg=file_arg)
    tasks = parse_pfyfile_text(src_text, task_sources)
    
    if tasks:
        resolved = _find_pfyfile(file_arg=file_arg)
        source = resolved if os.path.exists(resolved) else "embedded PFY_EMBED"
        
        # Group tasks by their source file
        from collections import defaultdict
        tasks_by_source = defaultdict(list)
        main_tasks = []
        
        for task in tasks.values():
            if task.source_file:
                tasks_by_source[task.source_file].append(task)
            else:
                main_tasks.append(task)
        
        # Print main tasks first
        if main_tasks:
            print(f"\nFrom {source}:")
            for task in main_tasks:
                if task.description:
                    print(f"  {task.name}  —  {task.description}")
                else:
                    print(f"  {task.name}")
        
        # Print tasks grouped by include file
        for source_file in sorted(tasks_by_source.keys()):
            # Generate subcommand name from filename
            basename = os.path.basename(source_file)
            # Remove Pfyfile. prefix and .pf suffix
            subcommand_name = basename
            if subcommand_name.startswith("Pfyfile."):
                subcommand_name = subcommand_name[8:]  # Remove "Pfyfile."
            if subcommand_name.endswith(".pf"):
                subcommand_name = subcommand_name[:-3]  # Remove ".pf"
            # Convert underscores to hyphens
            subcommand_name = subcommand_name.replace("_", "-")
            
            print(f"\n[{subcommand_name}] From {source_file}:")
            for task in sorted(tasks_by_source[source_file], key=lambda t: t.name):
                if task.description:
                    print(f"  {task.name}  —  {task.description}")
                else:
                    print(f"  {task.name}")
    
    if ENV_MAP:
        print("\nEnvironments:")
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
        
        # Handle --arg=value format
        if a.startswith("--") and "=" in a:
            k, v = a[2:].split("=", 1)  # Strip -- prefix and split
            if k == "hosts": host_specs.extend(_normalize_hosts(v))
            elif k == "host": host_specs.append(v.strip())
            elif k == "env": env_names.append(v.strip())
            elif k == "user": user = v
            elif k == "port": port = v
            elif k in ("sudo", "become"): sudo = v.lower() in ("1","true","yes","on")
            elif k in ("sudo_user", "become_user", "sudo-user", "become-user"): sudo_user = v
            else:
                tasks = argv[i:]; break
            i += 1; continue
        
        # Handle --arg value format
        if a.startswith("--") and i + 1 < len(argv):
            k = a[2:]  # Strip -- prefix
            # Special handling for --list and --help (treat as tasks)
            if k in ("list", "help"):
                tasks = argv[i:]; break
            # Check if next arg is a value (doesn't start with --)
            next_arg = argv[i + 1]
            if k in ("hosts", "host", "env", "user", "port", "sudo-user", "sudo_user", "become-user", "become_user") and not next_arg.startswith("--"):
                v = next_arg
                if k == "hosts": host_specs.extend(_normalize_hosts(v))
                elif k == "host": host_specs.append(v.strip())
                elif k == "env": env_names.append(v.strip())
                elif k == "user": user = v
                elif k == "port": port = v
                elif k in ("sudo_user", "become_user", "sudo-user", "become-user"): sudo_user = v
                i += 2; continue
            # Handle boolean flags like --sudo, --become
            elif k in ("sudo", "become"):
                sudo = True
                i += 1; continue
        
        # Handle --list and --help as standalone flags
        if a in ("--list", "--help", "-h"):
            tasks = argv[i:]; break
        
        # Handle legacy arg=value format (without --)
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
            print("Usage: pf [<pfy_file>] [env=NAME|--env=NAME|--env NAME]* [hosts=..|--hosts=..|--hosts ..] [user=..|--user=..|--user ..] [port=..|--port=..|--port ..] [sudo=true|--sudo] [sudo_user=..|--sudo-user=..|--sudo-user ..] <task|list|help> [more_tasks...]")
            print("\nAvailable tasks:")
            _print_list(file_arg=pfy_file_arg)
        return 0
    if tasks[0] in ("list", "--list"):
        _print_list(file_arg=pfy_file_arg); return 0

    # Resolve hosts
    env_hosts = _merge_env_hosts(env_names)
    merged_hosts = _dedupe_preserve_order(env_hosts + host_specs)
    if not merged_hosts:
        merged_hosts = ["@local"]

    # Load tasks once
    dsl_src, task_sources = _load_pfy_source_with_includes(file_arg=pfy_file_arg)
    dsl_tasks = parse_pfyfile_text(dsl_src, task_sources)
    valid_task_names = set(BUILTINS.keys()) | set(dsl_tasks.keys()) | {"list", "help", "--help", "--list"}

    # Parse multi-task + params: <task> [k=v ...] <task2> [k=v ...] ...
    selected = []
    j = 0
    all_names_for_alias = list(BUILTINS.keys()) + list(dsl_tasks.keys()) + ["list","help","--help","--list"]
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
        while j < len(tasks) and ("=" in tasks[j]):
            arg = tasks[j]
            # Support both --param=value and param=value formats
            if arg.startswith("--"):
                k, v = arg[2:].split("=", 1)  # Strip -- prefix
            else:
                k, v = arg.split("=", 1)
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
        connection, sflag, suser = ctuple if isinstance(ctuple, tuple) else (None, sudo, sudo_user)
        if connection is not None:
            try:
                connection.open()
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
                    rc = _exec_line_fabric(connection, ln, sflag, suser, prefix, params, task_env)
                    if rc != 0:
                        print(f"{prefix} !! command failed (rc={rc}): {ln}", file=sys.stderr)
                        return rc
                except Exception as e:
                    print(f"{prefix} !! error: {e}", file=sys.stderr)
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
            except Exception as e:
                print(f"[{h}] !! unhandled: {e}", file=sys.stderr)
                rc = 1
            rc_total = rc_total or rc

    return rc_total

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
