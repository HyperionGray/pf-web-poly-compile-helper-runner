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
import textwrap
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
DEFAULT_SHELL_TEMPLATE: Optional[str] = None
DEFAULT_SHELL_LANG: Optional[str] = None
PFY_ROOT: Optional[str] = None

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
    "fortran": _compile_profile(".f90", "gfortran {src} -o {bin}", "{bin}"),
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
}POLYGLOT_ALIASES = {
    "py": "python",
    "python3": "python",
    "shell": "bash",
    "sh": "sh",
    "zshell": "zsh",
    "golang": "go",
    "c++": "cpp",
    "cxx": "cpp",
    "clang": "c",
    "clang++": "cpp",
    "asm86": "asm",
    "fortran90": "fortran",
    "gfortran": "fortran",
    "java": "java-openjdk",
    "java-openjdk": "java-openjdk",
    "java-android-google": "java-android",
    "java-android": "java-android",
    "android-java": "java-android",
    "fishshell": "fish",
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
    def __init__(self, name: str):
        self.name = name
        self.lines: List[str] = []
        self.description: Optional[str] = None
    def add(self, line: str): self.lines.append(line)

def _read_text_file(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def _canonical_lang(name: str) -> str:
    lang_key = POLYGLOT_ALIASES.get(name.lower(), name.lower())
    if lang_key not in POLYGLOT_LANGS:
        raise ValueError(f"Unknown polyglot language: {name}")
    return lang_key


def _maybe_extract_shebang(text: str) -> str:
    """Support shebang-like directive (e.g., '#!fish' or '#!lang:python')."""
    global DEFAULT_SHELL_TEMPLATE, DEFAULT_SHELL_LANG
    lines = text.splitlines()
    idx = next((i for i, line in enumerate(lines) if line.strip()), None)
    if idx is None:
        return text
    first_stripped = lines[idx].strip()
    if first_stripped.startswith("#!"):
        directive = first_stripped[2:].strip()
        lower = directive.lower()
        if lower.startswith(("lang:", "language:", "polyglot:")):
            lang_part = directive.split(":", 1)[1].strip() if ":" in directive else ""
            DEFAULT_SHELL_LANG = _canonical_lang(lang_part) if lang_part else None
            DEFAULT_SHELL_TEMPLATE = None
        else:
            DEFAULT_SHELL_TEMPLATE = directive or None
            DEFAULT_SHELL_LANG = None
        del lines[idx]
        return "\n".join(lines)
    return text

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
    global DEFAULT_SHELL_TEMPLATE, DEFAULT_SHELL_LANG, PFY_ROOT
    DEFAULT_SHELL_TEMPLATE = None
    DEFAULT_SHELL_LANG = None
    PFY_ROOT = None
    pfy_resolved = _find_pfyfile(file_arg=file_arg)
    if os.path.exists(pfy_resolved):
        base_dir = os.path.dirname(os.path.abspath(pfy_resolved)) or "."
        PFY_ROOT = base_dir
        visited: set[str] = {os.path.abspath(pfy_resolved)}
        main_text = _read_text_file(pfy_resolved)
        main_text = _maybe_extract_shebang(main_text)
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

def _build_shell_invocation(cmd: str, template_override: Optional[str] = None) -> Tuple[List[str] | str, bool]:
    template = template_override or DEFAULT_SHELL_TEMPLATE or os.environ.get("PF_SHELL_TEMPLATE")
    if template:
        if "{cmd}" in template:
            return template.format(cmd=cmd), True
        parts = shlex.split(template)
    else:
        shell_env = os.environ.get("SHELL")
        if shell_env:
            parts = shlex.split(shell_env)
        else:
            return cmd, True
    exe = os.path.basename(parts[0])
    if exe.startswith("python"):
        return parts + ["-c", cmd], False
    shell_flags = {
        "bash": "-lc",
        "sh": "-lc",
        "zsh": "-lc",
        "ksh": "-lc",
        "fish": "-c",
    }
    flag = shell_flags.get(exe, "-c")
    return parts + [flag, cmd], False

def _run_local(cmd: str, env=None, shell_template: Optional[str] = None):
    import subprocess
    invocation, use_shell = _build_shell_invocation(cmd, template_override=shell_template)
    if use_shell:
        p = subprocess.Popen(invocation, shell=True, env=env)
    else:
        p = subprocess.Popen(invocation, shell=False, env=env)
    return p.wait()

def _sudo_wrap(cmd: str, sudo_user: Optional[str]) -> str:
    if sudo_user:
        return f"sudo -u {shlex.quote(sudo_user)} -H bash -lc {shlex.quote(cmd)}"
    return f"sudo bash -lc {shlex.quote(cmd)}"

def _exec_line_fabric(
    c: Optional[Connection],
    line: str,
    sudo: bool,
    sudo_user: Optional[str],
    prefix: str,
    params: dict,
    task_env: dict,
    shell_template: Optional[str],
    shell_lang: Optional[str],
):
    # interpolate & parse
    line = _interpolate(line, params, task_env)
    parts = shlex.split(line)
    if not parts: return 0

    def run(cmd: str, template_override: Optional[str] = None):
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
            effective_template = template_override if template_override is not None else shell_template
            return _run_local(full, env=merged_env, shell_template=effective_template)
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
        inline_template = None
        lang_used = None
        if args and args[0].startswith("[") and args[0].endswith("]"):
            inline_template = args[0][1:-1].strip()
            args = args[1:]
            if inline_template.lower() in {"default", "reset"}:
                inline_template = DEFAULT_SHELL_TEMPLATE
        cmd = " ".join(args)
        if inline_template:
            lang_hint = _parse_polyglot_template(inline_template)
            if lang_hint:
                rendered, lang_used = _render_polyglot_command(lang_hint, cmd, PFY_ROOT)
                cmd = rendered
                inline_template = None
        if not lang_used:
            default_lang = shell_lang or DEFAULT_SHELL_LANG
            if default_lang:
                rendered, lang_used = _render_polyglot_command(default_lang, cmd, PFY_ROOT)
                if rendered is not None:
                    cmd = rendered
                    inline_template = None
        if not cmd: raise ValueError("shell needs a command")
        return run(cmd, template_override=inline_template)

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

    if not tasks or tasks[0] in {"help", "--help"}:
        print("Usage: pf [<pfy_file>] [env=NAME]* [hosts=..|host=..]* [user=..] [port=..] [sudo=true] [sudo_user=..] <task|list> [more_tasks...]")
        print("\\nAvailable tasks:"); _print_list(file_arg=pfy_file_arg); return 0
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
            task_shell_template = DEFAULT_SHELL_TEMPLATE
            task_shell_lang = DEFAULT_SHELL_LANG
            for ln in lines:
                stripped = ln.strip()
                if stripped.startswith('env '):
                    for tok in shlex.split(stripped)[1:]:
                        if '=' in tok:
                            k,v = tok.split('=',1)
                            task_env[k] = _interpolate(v, params, task_env)
                    continue
                if stripped.startswith('shell_template'):
                    parts = shlex.split(stripped)
                    if len(parts) > 1:
                        candidate = " ".join(parts[1:])
                        if candidate.lower() in {"default", "reset"}:
                            task_shell_template = DEFAULT_SHELL_TEMPLATE
                        else:
                            task_shell_template = candidate
                    else:
                        task_shell_template = DEFAULT_SHELL_TEMPLATE
                    continue
                if stripped.startswith('shell_lang') or stripped.startswith('shell_language'):
                    parts = shlex.split(stripped)
                    if len(parts) > 1:
                        candidate = parts[1]
                        lower = candidate.lower()
                        if lower in {"default", "reset"}:
                            task_shell_lang = DEFAULT_SHELL_LANG
                        elif lower in {"none", "off", "clear"}:
                            task_shell_lang = None
                        else:
                            task_shell_lang = _canonical_lang(candidate)
                    else:
                        task_shell_lang = DEFAULT_SHELL_LANG
                    continue
                try:
                    rc = _exec_line_fabric(c, ln, sflag, suser, prefix, params, task_env, task_shell_template, task_shell_lang)
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
