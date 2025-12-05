#!/home/punk/.venv/bin/python
"""
- Symbol-free DSL: shell, packages install/remove, service start/stop/enable/disable/restart, directory, copy
- describe: one-line task description shows in `pf list`
- include: top-level includes (outside tasks) to split stacks
- Per-task params: pf run-tls tls_cert=... tls_key=... port=9443 (use $tls_cert in DSL)
- Per-task env: inside a task, `env KEY=VAL KEY2=VAL2` applies to subsequent lines in that task
- Envs/hosts: env=prod, hosts=user@ip:port,..., repeatable host=...
- Parallel SSH across hosts with prefixed live output
- Flexible help: support help, --help, -h, hlep, hepl, heelp, hlp variations
- Flexible parameters: --key=value, -k val, and key=value are equivalent

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
PFY_ROOT: Optional[str] = None  # Set by main() when loading the Pfyfile
ENV_MAP: Dict[str, List[str] | str] = {
    "local": ["@local"],
    "prod": ["ubuntu@10.0.0.5:22", "punk@10.4.4.4:24"],
    "staging": "staging@10.1.2.3:22,staging@10.1.2.4:22",
}

# Help command variations - common typos and alternatives
HELP_VARIATIONS = {"help", "--help", "-h", "hlep", "hepl", "heelp", "hlp"}


# ---------- Flexible help and parameter parsing ----------
def _normalize_help_option(arg: str) -> bool:
    """Check if an argument is a help option, including common typos."""
    help_variations = {
        'help', '--help', '-h', 'hlep', 'hepl', 'heelp', 'hlp',
        '--hlep', '--hepl', '--heelp', '--hlp'
    }
    return arg.lower() in help_variations


def _normalize_parameter_key(key: str) -> str:
    """Normalize parameter keys to handle variations."""
    # Handle common variations
    key_mappings = {
        'sudo_user': 'sudo-user',
        'become_user': 'become-user',
        'sudo-user': 'sudo-user',
        'become-user': 'become-user',
    }
    return key_mappings.get(key, key)


def _try_parse_parameter_formats(args: List[str], i: int) -> Tuple[Optional[Tuple[str, str]], int]:
    """
    Try to parse parameter in multiple formats:
    1. --key=value
    2. --key value
    3. -k value (single char)
    4. key=value
    
    Returns: ((key, value), new_index) or (None, original_index)
    """
    if i >= len(args):
        return None, i
        
    arg = args[i]
    
    # Format 1: --key=value or key=value
    if '=' in arg:
        if arg.startswith('--'):
            key, value = arg[2:].split('=', 1)
            return (_normalize_parameter_key(key), value), i + 1
        elif not arg.startswith('-'):
            key, value = arg.split('=', 1)
            return (_normalize_parameter_key(key), value), i + 1
    
    # Format 2: --key value
    if arg.startswith('--') and i + 1 < len(args):
        key = arg[2:]
        next_arg = args[i + 1]
        if not next_arg.startswith('-') and '=' not in next_arg:
            return (_normalize_parameter_key(key), next_arg), i + 2
    
    # Format 3: -k value (single character options)
    if arg.startswith('-') and len(arg) == 2 and i + 1 < len(args):
        short_key = arg[1]
        next_arg = args[i + 1]
        if not next_arg.startswith('-') and '=' not in next_arg:
            # Map common short options
            short_mappings = {
                'h': 'help',
                'f': 'file',
                'u': 'user',
                'p': 'port',
                'e': 'env',
            }
            key = short_mappings.get(short_key, short_key)
            return (_normalize_parameter_key(key), next_arg), i + 2
    
    return None, i


# ---------- Pfyfile discovery ----------
def _find_pfyfile(
    start_dir: Optional[str] = None, file_arg: Optional[str] = None
) -> str:
    if file_arg:
        if os.path.isabs(file_arg):
            return file_arg
        return os.path.abspath(file_arg)

    # Allow empty env to fall back to default
    pf_hint = os.environ.get("PFY_FILE") or "Pfyfile.pf"
    if os.path.isabs(pf_hint):
        return pf_hint
    cur = os.path.abspath(start_dir or os.getcwd())
    while True:
        candidate = os.path.join(cur, pf_hint)
        if os.path.isfile(candidate):
            return candidate
        parent = os.path.dirname(cur)
        if parent == cur:
            # Last resort: current working directory + default hint
            return os.path.join(os.getcwd(), pf_hint)
        cur = parent


# ---------- Interpolation ----------
_VAR_RE = re.compile(r"\$([a-zA-Z_][\w-]*)|\$\{([a-zA-Z_][\w-]*)\}")


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


def _build_script_command(
    interpreter_cmd: str,
    ext: str,
    code: str,
    args: List[str],
    basename: str = "pf_poly",
) -> str:
    code = _ensure_newline(code)
    arg_str = _poly_args(args)
    return (
        "tmpdir=$(mktemp -d)\n"
        f'src="$tmpdir/{basename}{ext}"\n'
        "cat <<'" + _POLY_DELIM + '\' > "$src"\n'
        f"{code}"
        + _POLY_DELIM
        + '\nchmod +x "$src" 2>/dev/null || true\n'
        + f'{interpreter_cmd} "$src"'
        + (f" {arg_str}" if arg_str else "")
        + '\nrc=$?\nrm -rf "$tmpdir"\nexit $rc\n'
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
        + '\' > "$src"\n'
        f"{code}"
        + _POLY_DELIM
        + "\n"
        + compiler
        + "\nrc=$?\n"
        + "if [ $rc -eq 0 ]; then\n"
        + f"  {runner}\n"
        + "  rc=$?\n"
        + "fi\n"
        + 'rm -rf "$tmpdir"\nexit $rc\n'
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
        + '\' > "$src"\n'
        + body
        + _POLY_DELIM
        + '\nnode "$src"'
        + (f" {arg_str}" if arg_str else "")
        + '\nrc=$?\nrm -rf "$tmpdir"\nexit $rc\n'
    )


def _script_profile(
    parts: List[str] | Tuple[str, ...], ext: str, basename: str = "pf_poly"
):
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
    "c-llvm": _compile_profile(
        ".c",
        "clang -x c -O3 -S -emit-llvm {src} -o {bin}.ll && cat {bin}.ll",
        "echo '(LLVM IR generated with O3 optimization)'",
    ),
    "cpp-llvm": _compile_profile(
        ".cc",
        "clang++ -O3 -S -emit-llvm {src} -o {bin}.ll && cat {bin}.ll",
        "echo '(LLVM IR generated with O3 optimization)'",
    ),
    "c-llvm-bc": _compile_profile(
        ".c",
        "clang -x c -O3 -c -emit-llvm {src} -o {bin}.bc && llvm-dis {bin}.bc -o {bin}.ll && cat {bin}.ll",
        "echo '(LLVM bitcode generated with O3 optimization)'",
    ),
    "cpp-llvm-bc": _compile_profile(
        ".cc",
        "clang++ -O3 -c -emit-llvm {src} -o {bin}.bc && llvm-dis {bin}.bc -o {bin}.ll && cat {bin}.ll",
        "echo '(LLVM bitcode generated with O3 optimization)'",
    ),
    "fortran": _compile_profile(".f90", "gfortran {src} -o {bin}", "{bin}"),
    "fortran-llvm": _compile_profile(
        ".f90",
        "flang -O3 {src} -S -emit-llvm -o {bin}.ll && cat {bin}.ll",
        "echo '(LLVM IR generated with O3 optimization)'",
    ),
    "asm": _compile_profile(".s", "clang -x assembler {src} -o {bin}", "{bin}"),
    "zig": _compile_profile(
        ".zig", "zig build-exe -O Debug -femit-bin={bin} {src}", "{bin}"
    ),
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
    m = re.match(
        r"^(?:lang|language|polyglot)\s*(?:[:=]|\s+)\s*(.+)$", stripped, re.IGNORECASE
    )
    if not m:
        return None
    return m.group(1).strip().lower()


def _canonical_lang(lang_hint: str) -> str:
    """
    Resolve a language hint to a canonical language key.
    Uses POLYGLOT_ALIASES to resolve aliases to their canonical form.

    Args:
        lang_hint: The language name or alias (e.g., 'py', 'python3', 'js')

    Returns:
        The canonical language key (e.g., 'python', 'node')

    Raises:
        ValueError: If the language is not recognized
    """
    lang = lang_hint.strip().lower()
    # Check if it's already a canonical language name
    if lang in POLYGLOT_LANGS:
        return lang
    # Check if it's an alias
    if lang in POLYGLOT_ALIASES:
        return POLYGLOT_ALIASES[lang]
    raise ValueError(f"Unsupported language: {lang_hint}")


# Regex to parse [lang:xxx] syntax from shell command
_LANG_BRACKET_RE = re.compile(r"^\s*\[lang:([^\]]+)\]\s*(.*)$", re.IGNORECASE)


def _parse_lang_bracket(cmd: str) -> Tuple[Optional[str], str]:
    """
    Parse [lang:xxx] syntax from the beginning of a shell command.

    Args:
        cmd: The command string that may start with [lang:xxx]

    Returns:
        Tuple of (language_name or None, remaining_command)

    Examples:
        "[lang:python] print('hello')" -> ("python", "print('hello')")
        "echo hello" -> (None, "echo hello")
    """
    match = _LANG_BRACKET_RE.match(cmd)
    if match:
        lang = match.group(1).strip()
        remaining = match.group(2)
        return lang, remaining
    return None, cmd


def _extract_polyglot_source(
    cmd: str, working_dir: Optional[str] = None
) -> Tuple[str, List[str], Optional[str]]:
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
        full_path = (
            rel_path if os.path.isabs(rel_path) else os.path.join(base_dir, rel_path)
        )
        if not os.path.exists(full_path):
            raise FileNotFoundError(f"polyglot source file not found: {full_path}")
        with open(full_path, "r", encoding="utf-8") as poly_file:
            code = poly_file.read()
        if tokens and tokens[0] == "--":
            tokens = tokens[1:]
        return code, tokens, full_path
    return cmd, [], None


def _render_polyglot_command(
    lang_hint: Optional[str], cmd: str, working_dir: Optional[str]
) -> Tuple[Optional[str], Optional[str]]:
    if not lang_hint:
        return None, None
    lang_key = _canonical_lang(lang_hint)
    # _canonical_lang validates that the language exists, but let's be extra safe
    if lang_key not in POLYGLOT_LANGS:
        raise ValueError(
            f"Language '{lang_key}' (from '{lang_hint}') has no builder registered"
        )
    builder = POLYGLOT_LANGS[lang_key]
    snippet, lang_args, _ = _extract_polyglot_source(cmd, working_dir)
    rendered = builder(snippet, lang_args)
    return rendered, lang_key


# ---------- DSL (include + describe) ----------
class Task:
    def __init__(
        self,
        name: str,
        source_file: Optional[str] = None,
        params: Optional[Dict[str, str]] = None,
    ):
        self.name = name
        self.lines: List[str] = []
        self.description: Optional[str] = None
        self.source_file = source_file  # Track which file this task came from
        self.params: Dict[str, str] = params or {}  # Default parameter values

    def add(self, line: str):
        self.lines.append(line)


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
                task_name, _ = _parse_task_definition(stripped)
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
    """Load Pfyfile with includes expanded, return (text, task_sources)"""
    pfy_resolved = _find_pfyfile(file_arg=file_arg)
    if os.path.exists(pfy_resolved):
        base_dir = os.path.dirname(os.path.abspath(pfy_resolved)) or "."
        visited: set[str] = {os.path.abspath(pfy_resolved)}
        main_text = _read_text_file(pfy_resolved)
        return _expand_includes_from_text(main_text, base_dir, visited)
    return PFY_EMBED, {}


def _parse_task_definition(line: str) -> Tuple[str, Dict[str, str]]:
    """
    Parse a task definition line to extract task name and parameters.

    Examples:
        "task my-task" -> ("my-task", {})
        "task my-task param1=value1" -> ("my-task", {"param1": "value1"})
        "task my-task param1=\"\" param2=default" -> ("my-task", {"param1": "", "param2": "default"})

    Returns:
        Tuple of (task_name, parameters_dict)
    """
    # Remove "task " prefix
    rest = line[5:].strip()
    if not rest:
        raise ValueError("Task name missing.")

    # Use shlex to properly handle quoted values
    try:
        tokens = shlex.split(rest)
    except ValueError:
        # If shlex fails, fall back to simple split
        tokens = rest.split()

    if not tokens:
        raise ValueError("Task name missing.")

    task_name = tokens[0]
    params: Dict[str, str] = {}

    # Parse parameter definitions (key=value pairs)
    for token in tokens[1:]:
        if "=" in token:
            key, value = token.split("=", 1)
            params[key] = value
        else:
            # If a token doesn't have '=', it might be part of task name (shouldn't happen with proper syntax)
            # For now, we'll just skip it to be lenient
            pass

    return task_name, params


def _process_line_continuation(lines: List[str], start_idx: int) -> Tuple[str, int]:
    """
    Process backslash line continuation starting from the given index.
    
    Args:
        lines: List of all lines (stripped)
        start_idx: Index of the first line to process
        
    Returns:
        Tuple of (combined_line, next_index_to_process)
    """
    combined_parts = []
    current_idx = start_idx
    
    while current_idx < len(lines):
        line = lines[current_idx]
        
        # Skip empty lines and comments during continuation
        if not line or line.startswith("#"):
            current_idx += 1
            continue
            
        # Check if this line ends with backslash (line continuation)
        if line.endswith("\\"):
            # Remove the backslash and add to combined parts
            line_without_backslash = line[:-1].rstrip()
            if line_without_backslash:  # Only add non-empty parts
                combined_parts.append(line_without_backslash)
            current_idx += 1
            continue
        else:
            # This line doesn't end with backslash, add it and we're done
            if line:  # Only add non-empty lines
                combined_parts.append(line)
            current_idx += 1
            break
    
    # Join all parts with single space, preserving the structure
    combined_line = " ".join(combined_parts) if combined_parts else ""
    return combined_line, current_idx


def parse_pfyfile_text(
    text: str, task_sources: Optional[Dict[str, str]] = None
) -> Dict[str, Task]:
    """Parse Pfyfile text into Task objects with optional source tracking.

    Supports bash-style backslash line continuation: lines ending with '\\'
    are joined with following lines until a line without trailing backslash.
    """
    tasks: Dict[str, Task] = {}
    cur: Optional[Task] = None
    
    # Pre-process all lines and strip them
    all_lines = [raw.strip() for raw in text.splitlines()]
    line_idx = 0
    
    while line_idx < len(all_lines):
        line = all_lines[line_idx]
        
        # Skip empty lines and comments at top level
        if not line or line.startswith("#"):
            line_idx += 1
            continue
            
        if line.startswith("task "):
            task_name, params = _parse_task_definition(line)
            # For task_sources lookup, we need to check both the full line and just the task name
            # Priority: exact match with full line, then just task name
            full_line = line.split(None, 1)[1].strip()
            source_file = None
            if task_sources:
                source_file = task_sources.get(full_line) or task_sources.get(task_name)
            cur = Task(task_name, source_file=source_file, params=params)
            tasks[task_name] = cur
            line_idx += 1
            continue
            
        if line == "end":
            # Handle incomplete continuation at task end
            if pending_continuation is not None and cur is not None:
                cur.add(pending_continuation)
                pending_continuation = None
            cur = None
            line_idx += 1
            continue
            
        if cur is None:
            line_idx += 1
            continue
            
        # Handle task body lines with potential line continuation
        if line.endswith("\\"):
            # This line has continuation, process it
            combined_line, next_idx = _process_line_continuation(all_lines, line_idx)
            if combined_line:  # Only add non-empty combined lines
                if combined_line.startswith("describe "):
                    if cur.description is None:
                        cur.description = combined_line.split(None, 1)[1].strip()
                else:
                    cur.add(combined_line)
            line_idx = next_idx
        else:
            # Regular line without continuation
            if line.startswith("describe "):
                if cur.description is None:
                    cur.description = line.split(None, 1)[1].strip()
            else:
                cur.add(line)
            line_idx += 1
            
    return tasks


def list_dsl_tasks_with_desc(
    file_arg: Optional[str] = None,
) -> List[Tuple[str, Optional[str]]]:
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
    if spec is None:
        return []
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
    seen = set()
    out = []
    for it in items:
        if it not in seen:
            seen.add(it)
            out.append(it)
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
    if h == "@local":
        return {"local": True}
    user = default_user
    port = default_port
    host = h
    if "@" in host:
        user, host = host.split("@", 1)
    if ":" in host:
        host, port = host.split(":", 1)
    return {
        "local": False,
        "user": user,
        "host": host,
        "port": int(port) if port else None,
    }


def _c_for(spec, sudo: bool, sudo_user: Optional[str]):
    if spec.get("local"):
        return None
    return (
        Connection(
            host=spec["host"],
            user=spec["user"],
            port=spec["port"] if spec["port"] else 22,
        ),
        sudo,
        sudo_user,
    )


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


def _exec_line_fabric(
    c: Optional[Connection],
    line: str,
    sudo: bool,
    sudo_user: Optional[str],
    prefix: str,
    params: dict,
    task_env: dict,
):
    # interpolate & parse
    line = _interpolate(line, params, task_env)

    # Extract the verb (first word) to determine the operation
    # For 'shell' commands, we preserve the rest of the line as-is to maintain bash syntax
    stripped = line.strip()
    if not stripped:
        return 0

    # Split at most once to get the verb and the rest
    parts_split = stripped.split(maxsplit=1)
    verb = parts_split[0]
    rest_of_line = parts_split[1] if len(parts_split) > 1 else ""

    def run(cmd: str):
        # Build environment for this command
        merged_env = dict(os.environ)
        if task_env:
            merged_env.update(
                {k: _interpolate(str(v), params, task_env) for k, v in task_env.items()}
            )
        # For remote, prefix with export; for local, pass env to subprocess
        if c is None:
            full = cmd if not sudo else _sudo_wrap(cmd, sudo_user)
            # Prepend exports for display only
            if task_env:
                exports = " ".join(
                    [f"{k}={shlex.quote(str(v))}" for k, v in task_env.items()]
                )
                display = f"{exports} {full}" if exports else full
            else:
                display = full
            print(f"{prefix}$ {display}")
            return _run_local(full, env=merged_env)
        else:
            exports = " ".join(
                [
                    f"export {k}={shlex.quote(str(v))};"
                    for k, v in (task_env or {}).items()
                ]
            )
            shown = f"{exports} {cmd}".strip()
            print(f"{prefix}$ {(('(sudo) ' + shown) if sudo else shown)}")
           then
        echo "RUN {install_deps}" >> "$DOCKERFILE"
    fi
    
    # Add build commands
    if [ -n "$BUILD_CMDS" ]; then
        echo "RUN $BUILD_CMDS" >> "$DOCKERFILE"
    fi
    
    # Add port if specified
    if [ -n "{port_hint}" ]; then
        echo "EXPOSE {port_hint}" >> "$DOCKERFILE"
    fi
    
    # Add run command
    if [ -n "$RUN_CMD" ]; then
        echo "CMD [\\"$RUN_CMD\\"]" >> "$DOCKERFILE"
    fi
    
    # Replace variables in Dockerfile
    sed -i "s|\\$BASE_IMAGE|$BASE_IMAGE|g" "$DOCKERFILE"
    
    echo ""
    echo "==> Generated Dockerfile:"
    cat "$DOCKERFILE"
    
    if [ "{dockerfile_only}" = "True" ]; then
        echo ""
        echo "✓ Dockerfile generated: $DOCKERFILE"
        exit 0
    fi
    
    # Build the container
    echo ""
    echo "==> Building container image..."
    
    # Prefer podman, fallback to docker
    if command -v podman &> /dev/null; then
        CONTAINER_RT="podman"
    elif command -v docker &> /dev/null; then
        CONTAINER_RT="docker"
    else
        echo "✗ Error: Neither podman nor docker found"
        exit 1
    fi
    
    $CONTAINER_RT build -t "$FULL_IMAGE" -f "$DOCKERFILE" .
    
    echo ""
    echo "✓ Container image built: $FULL_IMAGE"
    
    # Generate Quadlet file
    if [ "{quadlet_only}" != "True" ]; then
        QUADLET_FILE="$PROJECT_NAME.container"
        cat > "$QUADLET_FILE" << QUADLET_EOF
[Unit]
Description=$PROJECT_NAME container service
Documentation=https://github.com/containers/podman/blob/main/docs/source/markdown/podman-systemd.unit.5.md

[Container]
ContainerName=$PROJECT_NAME
Image=$FULL_IMAGE

Volume=$PROJECT_NAME-data:/app/data:rw,z

QUADLET_EOF

        if [ -n "{port_hint}" ]; then
            echo "PublishPort={port_hint}:{port_hint}" >> "$QUADLET_FILE"
        fi
        
        cat >> "$QUADLET_FILE" << QUADLET_EOF

Environment=TZ=UTC

NoNewPrivileges=true

Memory=512m
CPUQuota=100%

Label=app=$PROJECT_NAME
Label=generator=pf-containerize

Restart=always

[Install]
WantedBy=default.target
QUADLET_EOF

        echo "✓ Quadlet file generated: $QUADLET_FILE"
    fi
    
    # Clean up
    rm -f "$DOCKERFILE"
fi

echo ""
echo "==> Containerization complete!"
"""
        return run(containerize_script)

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
    "autobuild-retry": [
        "autobuild_retry",
    ],
    "build_detect": [
        "build_detect",
    ],
    "containerize": [
        "containerize",
    ],
    "auto-container": [
        "containerize",
    ],
}


# ---------- CLI ----------
def _group_tasks_by_prefix(tasks_list: List) -> Tuple[List, Dict[str, List]]:
    """
    Group tasks by their prefix (e.g., 'road-block' -> 'road' group).
    
    Returns:
        Tuple of (ungrouped_tasks, grouped_tasks_dict)
    """
    from collections import defaultdict
    
    prefix_counts = defaultdict(list)
    ungrouped = []
    
    for task in tasks_list:
        name = task.name
        # Check if task name has a prefix (contains hyphen or underscore)
        if "-" in name:
            prefix = name.split("-")[0]
            prefix_counts[prefix].append(task)
        elif "_" in name:
            prefix = name.split("_")[0]
            prefix_counts[prefix].append(task)
        else:
            ungrouped.append(task)
    
    # Only group if there are 2+ tasks with the same prefix
    grouped = {}
    for prefix, task_list in prefix_counts.items():
        if len(task_list) >= 2:
            grouped[prefix] = task_list
        else:
            # If only one task with this prefix, treat as ungrouped
            ungrouped.extend(task_list)
    
    return ungrouped, grouped


def _print_list(file_arg: Optional[str] = None):
    """Print available tasks grouped by source and by prefix"""
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

        # Print main tasks first, grouped by prefix
        if main_tasks:
            print(f"\nFrom {source}:")
            ungrouped, grouped = _group_tasks_by_prefix(main_tasks)
            
            # Print ungrouped tasks first
            for task in sorted(ungrouped, key=lambda t: t.name):
                if task.description:
                    print(f"  {task.name}  —  {task.description}")
                else:
                    print(f"  {task.name}")
            
            # Print grouped tasks by prefix
            for prefix in sorted(grouped.keys()):
                print(f"\n  [{prefix}]")
                for task in sorted(grouped[prefix], key=lambda t: t.name):
                    if task.description:
                        print(f"    {task.name}  —  {task.description}")
                    else:
                        print(f"    {task.name}")

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
            source_tasks = tasks_by_source[source_file]
            ungrouped, grouped = _group_tasks_by_prefix(source_tasks)
            
            # Print ungrouped tasks first
            for task in sorted(ungrouped, key=lambda t: t.name):
                if task.description:
                    print(f"  {task.name}  —  {task.description}")
                else:
                    print(f"  {task.name}")
            
            # Print grouped tasks by prefix
            for prefix in sorted(grouped.keys()):
                print(f"\n  [{prefix}]")
                for task in sorted(grouped[prefix], key=lambda t: t.name):
                    if task.description:
                        print(f"    {task.name}  —  {task.description}")
                    else:
                        print(f"    {task.name}")

    if ENV_MAP:
        print("\nEnvironments:")
        for k, v in ENV_MAP.items():
            vs = _normalize_hosts(v)
            print(f"  {k}: {', '.join(vs) if vs else '(empty)'}")


def _print_task_help(task_name: str, file_arg: Optional[str] = None) -> int:
    """Print detailed help for a specific task.
    
    Returns:
        0 if task was found, 1 if task was not found.
    """
    # Load tasks
    dsl_src, task_sources = _load_pfy_source_with_includes(file_arg=file_arg)
    dsl_tasks = parse_pfyfile_text(dsl_src, task_sources)
    
    # Check builtins first
    if task_name in BUILTINS:
        print(f"Built-in task: {task_name}")
        print("\nCommands:")
        for line in BUILTINS[task_name]:
            print(f"  {line}")
        return 0
    
    # Check DSL tasks
    if task_name in dsl_tasks:
        task = dsl_tasks[task_name]
        print(f"Task: {task_name}")
        if task.description:
            print(f"Description: {task.description}")
        if task.source_file:
            print(f"Source: {task.source_file}")
        if task.params:
            print("\nParameters:")
            for param, default in task.params.items():
                print(f"  {param}={default}")
        print("\nCommands:")
        for line in task.lines:
            print(f"  {line}")
        return 0
    
    # Task not found - suggest similar tasks
    import difflib
    all_tasks = list(BUILTINS.keys()) + list(dsl_tasks.keys())
    suggestions = difflib.get_close_matches(task_name, all_tasks, n=5, cutoff=0.4)
    
    print(f"Task '{task_name}' not found.", file=sys.stderr)
    if suggestions:
        print("Did you mean:", file=sys.stderr)
        for s in suggestions:
            print(f"  {s}", file=sys.stderr)
    return 1


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

    if (
        argv
        and not "=" in argv[0]
        and (os.path.exists(argv[0]) or argv[0].endswith(".pf"))
    ):
        pfy_file_arg = argv[0]
        argv = argv[1:]

    tasks: List[str] = []
    i = 0
    while i < len(argv):
        a = argv[i]

        # Handle --arg=value format
        if a.startswith("--") and "=" in a:
            k, v = a[2:].split("=", 1)  # Strip -- prefix and split
            if k == "hosts":
                host_specs.extend(_normalize_hosts(v))
            elif k == "host":
                host_specs.append(v.strip())
            elif k == "env":
                env_names.append(v.strip())
            elif k == "user":
                user = v
            elif k == "port":
                port = v
            elif k in ("sudo", "become"):
                sudo = v.lower() in ("1", "true", "yes", "on")
            elif k in ("sudo_user", "become_user", "sudo-user", "become-user"):
                sudo_user = v
            else:
                tasks = argv[i:]
                break
            i += 1
            continue

        # Handle --arg value format
        if a.startswith("--") and i + 1 < len(argv):
            k = a[2:]  # Strip -- prefix
            # Special handling for --list and --help (treat as tasks)
            if k in ("list", "help"):
                tasks = argv[i:]
                break
            # Check if next arg is a value (doesn't start with --)
            next_arg = argv[i + 1]
            if k in (
                "hosts",
                "host",
                "env",
                "user",
                "port",
                "sudo-user",
                "sudo_user",
                "become-user",
                "become_user",
            ) and not next_arg.startswith("--"):
                v = next_arg
                if k == "hosts":
                    host_specs.extend(_normalize_hosts(v))
                elif k == "host":
                    host_specs.append(v.strip())
                elif k == "env":
                    env_names.append(v.strip())
                elif k == "user":
                    user = v
                elif k == "port":
                    port = v
                elif k in ("sudo_user", "become_user", "sudo-user", "become-user"):
                    sudo_user = v
                i += 2
                continue
            # Handle boolean flags like --sudo, --become
            elif k in ("sudo", "become"):
                sudo = True
                i += 1
                continue

        # Handle --list and --help as standalone flags
        # Also handle help variations like hlep, hepl, heelp, hlp
        if a in ("--list",) or a in HELP_VARIATIONS:
            tasks = argv[i:]
            break

        # Handle legacy arg=value format (without --)
        if "=" in a and not a.startswith("--"):
            k, v = a.split("=", 1)
            if k == "hosts":
                host_specs.extend(_normalize_hosts(v))
            elif k == "host":
                host_specs.append(v.strip())
            elif k == "env":
                env_names.append(v.strip())
            elif k == "user":
                user = v
            elif k == "port":
                port = v
            elif k in ("sudo", "become"):
                sudo = v.lower() in ("1", "true", "yes", "on")
            elif k in ("sudo_user", "become_user"):
                sudo_user = v
            else:
                tasks = argv[i:]
                break
            i += 1
            continue

        if a == "--":
            tasks = argv[i + 1 :]
            break
        tasks = argv[i:]
        break

    if not tasks or tasks[0] in HELP_VARIATIONS:
        if len(tasks) > 1:
            return _print_task_help(tasks[1], file_arg=pfy_file_arg)
        else:
            print(
                "Usage: pf [<pfy_file>] [env=NAME|--env=NAME|--env NAME]* [hosts=..|--hosts=..|--hosts ..] [user=..|--user=..|--user ..] [port=..|--port=..|--port ..] [sudo=true|--sudo] [sudo_user=..|--sudo-user=..|--sudo-user ..] <task|list|help> [more_tasks...]"
            )
            print("\nAvailable tasks:")
            _print_list(file_arg=pfy_file_arg)
        return 0
    if tasks[0] in ("list", "--list"):
        _print_list(file_arg=pfy_file_arg)
        return 0

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
        | {"list", "--list"}
        | HELP_VARIATIONS
    )

    # Parse multi-task + params: <task> [k=v ...] <task2> [k=v ...] ...
    selected = []
    j = 0
    all_names_for_alias = (
        list(BUILTINS.keys())
        + list(dsl_tasks.keys())
        + ["list", "--list"]
        + list(HELP_VARIATIONS)
    )
    aliasmap_all = _alias_map(all_names_for_alias)
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
                    tname, list(valid_task_names), n=3, cutoff=0.5
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
            # Value shouldn't start with - or -- (another flag) or be a task name
            return not next_arg.startswith("-") and next_arg not in valid_task_names

        while j < len(tasks):
            arg = tasks[j]
            # Check if this looks like the next task name
            if not arg.startswith("-") and "=" not in arg and arg in valid_task_names:
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
                print(f"{prefix} connect error: {e}", file=sys.stderr)
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
                        connection, ln, sflag, suser, prefix, params, task_env
                    )
                    if rc != 0:
                        print(
                            f"{prefix} !! command failed (rc={rc}): {ln}",
                            file=sys.stderr,
                        )
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
