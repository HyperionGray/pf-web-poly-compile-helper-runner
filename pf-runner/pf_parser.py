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

File Structure (1939 lines, organized into sections):
  - CONFIG (lines 73-88): Environment and configuration
  - Pfyfile discovery (lines 90-113): Find and locate Pfyfile.pf
  - Interpolation (lines 115-133): Variable substitution
  - Polyglot shell helpers (lines 135-600): 40+ language support [465 lines]
  - DSL parsing (lines 601-937): Task definition parsing
  - Embedded sample (lines 939-946): Default task examples
  - Hosts parsing (lines 948-981): SSH host management
  - Executors (lines 983-1219): Fabric-based execution
  - Built-ins (lines 1221-1247): Default tasks
  - CLI (lines 1249+): Command-line interface

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

# ---------- CONFIG ----------
PFY_FILE = os.environ.get("PFY_FILE", "Pfyfile.pf")
PFY_ROOT: Optional[str] = None  # Set by main() when loading the Pfyfile
ENV_MAP: Dict[str, List[str] | str] = {
    "local": ["@local"],
    "prod": ["ubuntu@10.0.0.5:22", "punk@10.4.4.4:24"],
    "staging": "staging@10.1.2.3:22,staging@10.1.2.4:22",
}

# Import HELP_VARIATIONS from pf_args to avoid duplication
try:
    from pf_args import HELP_VARIATIONS
except ImportError:
    # Fallback for standalone use
    HELP_VARIATIONS = {"help", "--help", "-h", "hlep", "hepl", "heelp", "hlp"}


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

# Pattern for parsing [alias xxx] blocks in task definitions
_ALIAS_BLOCK_RE = re.compile(r"\[([^\]]+)\]")


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
    raise PFExecutionError(
        message=f"Unsupported language: {lang_hint}",
        suggestion=f"Supported languages: {', '.join(sorted(POLYGLOT_LANGS.keys()))}",
        command=f"shell_lang {lang_hint}"
    )


# Regex to parse [lang:xxx] syntax from shell command
# re.DOTALL makes . match newlines, allowing multi-line code blocks
_LANG_BRACKET_RE = re.compile(r"^\s*\[lang:([^\]]+)\]\s*(.*)$", re.IGNORECASE | re.DOTALL)

# Regex to parse heredoc syntax: << DELIMITER [> output_file]
# Allow uppercase or mixed case delimiters (following bash convention)
_HEREDOC_RE = re.compile(r"<<\s*([A-Za-z][A-Za-z0-9_]*)\s*(?:>\s*([^\s]+))?$")


def _parse_heredoc_syntax(cmd: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Parse heredoc syntax from a command line.
    
    Args:
        cmd: The command string that may contain << DELIMITER [> output_file]
    
    Returns:
        Tuple of (delimiter or None, output_file or None)
    
    Examples:
        "<< PYEOF" -> ("PYEOF", None)
        "<< PYEOF > output.txt" -> ("PYEOF", "output.txt")
        "print('hello')" -> (None, None)
    """
    match = _HEREDOC_RE.search(cmd)
    if match:
        delimiter = match.group(1)
        output_file = match.group(2) if match.group(2) else None
        return delimiter, output_file
    return None, None


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
        raise PFSyntaxError(
            message="Polyglot shell requires code or @file reference",
            suggestion="Provide inline code or use @filename syntax"
        )
    if raw.startswith("@") or raw.startswith("file:"):
        tokens = shlex.split(cmd)
        if not tokens:
            raise PFSyntaxError(
                message="Polyglot file token missing",
                suggestion="Use syntax: shell_lang python @script.py"
            )
        source_token = tokens.pop(0)
        if source_token.startswith("@"):
            rel_path = source_token[1:]
        else:
            rel_path = source_token[5:]
        full_path = (
            rel_path if os.path.isabs(rel_path) else os.path.join(base_dir, rel_path)
        )
        if not os.path.exists(full_path):
            raise PFSyntaxError(
                message=f"Polyglot source file not found: {full_path}",
                file_path=full_path,
                suggestion="Check that the file path is correct and the file exists"
            )
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
        raise PFExecutionError(
            message=f"Language '{lang_key}' (from '{lang_hint}') has no builder registered",
            suggestion=f"Supported languages: {', '.join(sorted(POLYGLOT_LANGS.keys()))}"
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
        aliases: Optional[List[str]] = None,
    ):
        self.name = name
        self.lines: List[str] = []
        self.description: Optional[str] = None
        self.source_file = source_file  # Track which file this task came from
        self.params: Dict[str, str] = params or {}  # Default parameter values
        self.aliases: List[str] = aliases or []  # Command aliases for this task
        
        # Enhanced documentation metadata
        self.synopsis: Optional[str] = None  # Brief usage synopsis
        self.category: Optional[str] = None  # Task category (e.g., "Security", "Build")
        self.examples: List[str] = []  # Usage examples
        self.prerequisites: List[str] = []  # Required tools/setup
        self.troubleshooting: List[str] = []  # Common issues and fixes
        self.see_also: List[str] = []  # Related tasks
        self.use_cases: List[str] = []  # When to use this task
        self.notes: List[str] = []  # Additional notes and warnings
        self.tags: List[str] = []  # Searchable tags

    def add(self, line: str):
        self.lines.append(line)
        
    def add_example(self, example: str):
        """Add a usage example."""
        self.examples.append(example)
        
    def add_prerequisite(self, prereq: str):
        """Add a prerequisite."""
        self.prerequisites.append(prereq)
        
    def add_troubleshooting(self, issue: str):
        """Add a troubleshooting tip."""
        self.troubleshooting.append(issue)
        
    def add_see_also(self, task: str):
        """Add a related task reference."""
        self.see_also.append(task)
        
    def add_use_case(self, use_case: str):
        """Add a use case description."""
        self.use_cases.append(use_case)
        
    def add_note(self, note: str):
        """Add a note or warning."""
        self.notes.append(note)
        
    def add_tag(self, tag: str):
        """Add a searchable tag."""
        if tag not in self.tags:
            self.tags.append(tag)


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
        base_dir = os.path.dirname(os.path.abspath(pfy_resolved)) or "."
        visited: set[str] = {os.path.abspath(pfy_resolved)}
        main_text = _read_text_file(pfy_resolved)
        user_text, user_sources = _expand_includes_from_text(main_text, base_dir, visited)
        
        # Merge task sources
        combined_sources = {}
        combined_sources.update(always_available_sources)
        combined_sources.update(user_sources)
        
        # Combine texts: always-available first, then user's tasks
        combined_text = always_available_text + "\n\n" + user_text
        return combined_text, combined_sources
    
    # No Pfyfile found - return always-available tasks only (or PFY_EMBED if that doesn't exist)
    if always_available_text:
        return always_available_text, always_available_sources
    return PFY_EMBED, {}


def _parse_task_definition(line: str) -> Tuple[str, Dict[str, str], List[str]]:
    """
    Parse a task definition line to extract task name, parameters, and aliases.

    Examples:
        "task my-task" -> ("my-task", {}, [])
        "task my-task param1=value1" -> ("my-task", {"param1": "value1"}, [])
        "task my-task param1=\"\" param2=default" -> ("my-task", {"param1": "", "param2": "default"}, [])
        "task long-command [alias cmd]" -> ("long-command", {}, ["cmd"])
        "task long-command [alias=cmd]" -> ("long-command", {}, ["cmd"])
        "task long-command [alias cmd|alias=c]" -> ("long-command", {}, ["cmd", "c"])

    Returns:
        Tuple of (task_name, parameters_dict, aliases_list)
    """
    # Remove "task " prefix
    rest = line[5:].strip()
    if not rest:
        raise PFSyntaxError(
            message="Task name missing",
            suggestion="Task definition format: task task-name [param=\"value\"]"
        )

    # Extract aliases from [...] blocks first
    aliases: List[str] = []

    # Find all [...] blocks and extract aliases
    for match in _ALIAS_BLOCK_RE.finditer(rest):
        block_content = match.group(1)
        # Split by | for multiple aliases in one block
        parts = block_content.split("|")
        for part in parts:
            part = part.strip()
            # Handle both "alias cmd" and "alias=cmd" formats
            if part.startswith("alias "):
                alias_name = part[6:].strip()
                if alias_name:
                    aliases.append(alias_name)
            elif part.startswith("alias="):
                alias_name = part[6:].strip()
                if alias_name:
                    aliases.append(alias_name)

    # Remove [...] blocks from the line for further parsing
    rest_without_aliases = _ALIAS_BLOCK_RE.sub("", rest).strip()

    # Use shlex to properly handle quoted values
    try:
        tokens = shlex.split(rest_without_aliases)
    except ValueError as e:
        raise PFSyntaxError(
            message=f"Failed to parse task definition: {e}",
            suggestion="Check for unclosed quotes or invalid escape sequences"
        )

    if not tokens:
        raise PFSyntaxError(
            message="Task name missing after parsing",
            suggestion="Task definition format: task task-name [param=\"value\"]"
        )

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

    return task_name, params, aliases


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
    are joined with following lines until a line without trailing backeturn 1
    """

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
                        connection, ln, sflag, suser, prefix, params, task_env
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
