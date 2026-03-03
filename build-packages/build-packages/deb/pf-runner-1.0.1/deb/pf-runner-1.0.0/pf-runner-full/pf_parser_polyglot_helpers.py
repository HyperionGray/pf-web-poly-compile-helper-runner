#!/usr/bin/env python3
"""
pf_parser_polyglot_helpers.py - Polyglot helpers extracted from pf_parser.
"""

import os
import re
import shlex
import textwrap
from typing import List, Dict, Tuple, Optional, Callable

import pf_config

from pf_parser_config import _ensure_config_loaded, _PF_CONFIG, PFY_ROOT

# Import custom exceptions
try:
    from pf_exceptions import PFSyntaxError, PFExecutionError
except ImportError:
    # Fallback for standalone use
    class PFSyntaxError(Exception):
        def __init__(self, message, file_path=None, suggestion=None, **_kwargs):
            super().__init__(message)
            self.file_path = file_path
            self.suggestion = suggestion

    class PFExecutionError(Exception):
        def __init__(self, message, suggestion=None, **_kwargs):
            super().__init__(message)
            self.suggestion = suggestion


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
    _ensure_config_loaded()
    headful = pf_config.get_bool(_PF_CONFIG or {}, "runner.playwright.headful", False)
    headless_js = "false" if headful else "true"
    snippet = textwrap.indent(code, "  ")
    body = (
        "const { chromium } = require('playwright');\n"
        "(async () => {\n"
        f"  const browser = await chromium.launch({{ headless: {headless_js} }});\n"
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
src=\"$tmpdir/Main.java\"
classes=\"$tmpdir/classes\"
dexdir=\"$tmpdir/dex\"
mkdir -p \"$classes\" \"$dexdir\"
cat <<'{_POLY_DELIM}' > \"$src\"
{code}{_POLY_DELIM}

ANDROID_SDK=\"${{ANDROID_SDK_ROOT:-${{ANDROID_HOME:-}}}}\"
platform_jar=\"${{ANDROID_PLATFORM_JAR:-}}\"
if [ -z \"$platform_jar\" ] && [ -n \"$ANDROID_SDK\" ]; then
  latest_platform=$(ls -1 \"$ANDROID_SDK/platforms\" 2>/dev/null | sort -V | tail -1)
  if [ -n \"$latest_platform\" ] && [ -f \"$ANDROID_SDK/platforms/$latest_platform/android.jar\" ]; then
    platform_jar=\"$ANDROID_SDK/platforms/$latest_platform/android.jar\"
  fi
fi
javac_cp=\"\"
if [ -n \"$platform_jar\" ] && [ -f \"$platform_jar\" ]; then
  javac_cp=\"-classpath $platform_jar\"
fi
javac $javac_cp -d \"$classes\" \"$src\"
rc=$?
if [ $rc -ne 0 ]; then
  rm -rf \"$tmpdir\"
  exit $rc
fi

d8_bin=\"${{ANDROID_D8:-}}\"
if [ -z \"$d8_bin\" ] && [ -n \"$ANDROID_SDK\" ]; then
  latest_bt=$(ls -1 \"$ANDROID_SDK/build-tools\" 2>/dev/null | sort -V | tail -1)
  if [ -n \"$latest_bt\" ] && [ -x \"$ANDROID_SDK/build-tools/$latest_bt/d8\" ]; then
    d8_bin=\"$ANDROID_SDK/build-tools/$latest_bt/d8\"
  fi
fi

if [ -n \"$d8_bin\" ] && command -v dalvikvm >/dev/null 2>&1; then
  \"$d8_bin\" --output \"$dexdir\" \"$classes\" >/dev/null
  rc=$?
  if [ $rc -eq 0 ]; then
    dalvikvm -cp \"$dexdir/classes.dex\" Main{" " + arg_str if arg_str else ""}
    rc=$?
    rm -rf \"$tmpdir\"
    exit $rc
  fi
fi

(cd \"$classes\" && java Main{" " + arg_str if arg_str else ""})
rc=$?
rm -rf \"$tmpdir\"
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
    "fortran": _compile_profile(
        ".f90",
        "gfortran {src} -o {bin}",
        "{bin}",
    ),
    "fortran-llvm": _compile_profile(
        ".f90",
        "flang -O3 -S -emit-llvm {src} -o {bin}.ll && cat {bin}.ll",
        "echo '(LLVM IR generated with O3 optimization)'",
    ),
    "zig": _compile_profile(
        ".zig",
        "zig build-exe {src} -O ReleaseFast -femit-bin={bin}",
        "{bin}",
    ),
    "nim": _compile_profile(
        ".nim",
        "nim c -d:release --out:{bin} {src}",
        "{bin}",
    ),
    "crystal": _compile_profile(
        ".cr",
        "crystal build {src} -o {bin}",
        "{bin}",
    ),
    "haskell-compile": _compile_profile(
        ".hs",
        "ghc -o {bin} {src}",
        "{bin}",
    ),
    "ocamlc": _compile_profile(
        ".ml",
        "ocamlc -o {bin} {src}",
        "{bin}",
    ),
    "asm": _compile_profile(
        ".s",
        "nasm -f elf64 {src} -o {bin}.o && ld {bin}.o -o {bin}",
        "{bin}",
    ),
    # Browser JS (playwright)
    "browser-js": lambda code, args: _build_browser_js_command(code, args),
    # JVM
    "java": _java_openjdk_builder(),
    "java-openjdk": _java_openjdk_builder(),
    "java-android": _java_android_builder(),
}


POLYGLOT_ALIASES = {
    "bash": "bash",
    "sh": "sh",
    "shell": "sh",
    "posix": "sh",
    "zsh": "zsh",
    "fish": "fish",
    "python": "python",
    "py": "python",
    "python3": "python",
    "node": "node",
    "nodejs": "node",
    "javascript": "node",
    "js": "node",
    "deno": "deno",
    "ts": "deno",
    "typescript": "deno",
    "ts-node": "ts-node",
    "perl": "perl",
    "php": "php",
    "ruby": "ruby",
    "rb": "ruby",
    "r": "r",
    "julia": "julia",
    "hs": "haskell",
    "haskell": "haskell",
    "haskell-compile": "haskell-compile",
    "ocaml": "ocaml",
    "ml": "ocaml",
    "elixir": "elixir",
    "exs": "elixir",
    "dart": "dart",
    "lua": "lua",
    "go": "go",
    "golang": "go",
    "rust": "rust",
    "rs": "rust",
    "c": "c",
    "c99": "c",
    "c11": "c",
    "cpp": "cpp",
    "c++": "cpp",
    "cc": "cpp",
    "cxx": "cpp",
    "fortran": "fortran",
    "f90": "fortran",
    "fortran-llvm": "fortran-llvm",
    "zig": "zig",
    "nim": "nim",
    "crystal": "crystal",
    "ocamlc": "ocamlc",
    "asm": "asm",
    "browser": "browser-js",
    "browser-js": "browser-js",
    "java": "java",
    "openjdk": "java",
    "java-openjdk": "java-openjdk",
    "android": "java-android",
    "java-android": "java-android",
}


def _parse_polyglot_template(template: str) -> Optional[str]:
    s = template.strip()
    if not s:
        return None
    if s.startswith("<<"):
        return None
    if s.startswith("@"):  # file reference
        return s
    return template


def _canonical_lang(lang_hint: str) -> str:
    lang_key = lang_hint.strip().lower()
    return POLYGLOT_ALIASES.get(lang_key, lang_key)


_LANG_BRACKET_RE = re.compile(r"^\s*\[lang:([^\]]+)\]\s*(.*)$", re.IGNORECASE | re.DOTALL)
_HEREDOC_RE = re.compile(r"<<\s*([A-Za-z][A-Za-z0-9_]*)\s*(?:>\s*([^\s]+))?$")
_POLYGLOT_HEREDOC_HEADER_RE = re.compile(
    r"^\s*<<-?\s*([A-Za-z][A-Za-z0-9_]*)\s*(?:>\s*([^\s]+))?\s*$"
)
_SHELL_LANG_BLOCK_RE = re.compile(
    r"^shell_lang\s+([^\s]+)\s+BLOCK(?:\s+#.*)?$", re.IGNORECASE
)
_SHELL_LANG_BLOCK_END_RE = re.compile(r"^ENDBLOCK(?:\s+#.*)?$", re.IGNORECASE)


def _parse_heredoc_syntax(cmd: str) -> Tuple[Optional[str], Optional[str]]:
    cmd = cmd.strip()
    match = _HEREDOC_RE.search(cmd)
    if not match:
        return None, None
    return match.group(1), match.group(2)


def _parse_lang_bracket(cmd: str) -> Tuple[Optional[str], str]:
    match = _LANG_BRACKET_RE.match(cmd)
    if not match:
        return None, cmd
    return match.group(1).strip(), match.group(2)


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


def _extract_polyglot_heredoc(cmd: str) -> Optional[Tuple[str, Optional[str]]]:
    """
    Extract a polyglot heredoc body from a command string.

    Supported forms:
      << DELIM
      <code>
      DELIM

      << DELIM > /path/to/output.txt
      <code>
      DELIM
    """
    if "\n" not in cmd:
        return None

    lines = cmd.splitlines()
    if not lines:
        return None

    header = lines[0].strip()
    m = _POLYGLOT_HEREDOC_HEADER_RE.match(header)
    if not m:
        return None

    delimiter = m.group(1)
    output_path = m.group(2)

    terminator_idx = None
    for idx in range(1, len(lines)):
        if lines[idx].strip() == delimiter:
            terminator_idx = idx
            break

    if terminator_idx is None:
        raise PFExecutionError(
            message=f"Unclosed heredoc: missing terminator '{delimiter}'",
            command=header,
            suggestion=f"Add a line containing only {delimiter} to close the heredoc",
        )

    code = "\n".join(lines[1:terminator_idx])
    if code and not code.endswith("\n"):
        code += "\n"
    return code, output_path


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
