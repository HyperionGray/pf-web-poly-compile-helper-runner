#!/usr/bin/env python3
"""
pf_polyglot.py - Polyglot language support for pf runner

This module provides support for 40+ programming languages through:
- Language detection and canonicalization
- Code execution builders for interpreted and compiled languages
- Template-based script generation
- Argument handling and shell escaping

Extracted from pf_parser.py to improve modularity and maintainability.

Supported Languages:
- Shells: bash, sh, dash, zsh, fish, ksh, tcsh, pwsh
- Interpreted: python, node, deno, perl, php, ruby, r, julia, haskell, ocaml, elixir, dart, lua
- Compiled: go, rust, c, cpp, fortran, zig, nim, crystal, haskell-compile, ocamlc
- JVM: java-openjdk, java-android
- Special: c-llvm, cpp-llvm, c-llvm-bc, cpp-llvm-bc, fortran-llvm, asm
"""

import os
import re
import shlex
import textwrap
from typing import List, Dict, Tuple, Optional, Callable

# Import custom exceptions
try:
    from pf_exceptions import PFSyntaxError, PFExecutionError
except ImportError:
    # Fallback for standalone use
    class PFSyntaxError(Exception):
        def __init__(self, message, file_path=None, suggestion=None):
            super().__init__(message)
            self.file_path = file_path
            self.suggestion = suggestion
    
    class PFExecutionError(Exception):
        def __init__(self, message, suggestion=None):
            super().__init__(message)
            self.suggestion = suggestion


# ---------- Polyglot Constants ----------
_POLY_DELIM = "__PFY_LANG__"


# ---------- Helper Functions ----------
def _cmd_str(parts: List[str] | Tuple[str, ...]) -> str:
    """Convert command parts to shell-quoted string."""
    return " ".join(shlex.quote(p) for p in parts)


def _poly_args(args: List[str]) -> str:
    """Convert arguments to shell-quoted string."""
    cleaned = [a for a in args if a]
    return " ".join(shlex.quote(a) for a in cleaned)


def _ensure_newline(src: str) -> str:
    """Ensure source code ends with newline."""
    return src if src.endswith("\n") else f"{src}\n"


def _build_script_command(
    interpreter_cmd: str,
    ext: str,
    code: str,
    args: List[str],
    basename: str = "pf_poly",
) -> str:
    """Build shell command for interpreted languages."""
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
    """Build shell command for compiled languages."""
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
    """Build command for browser JavaScript using Playwright."""
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


# ---------- Builder Factories ----------
def _script_profile(
    parts: List[str] | Tuple[str, ...], ext: str, basename: str = "pf_poly"
):
    """Create builder for interpreted languages."""
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
    """Create builder for compiled languages."""
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
    """Create builder for OpenJDK Java."""
    return _compile_profile(
        ".java",
        "javac -d {classes} {src}",
        "(cd {classes} && java Main{args})",
        setup_lines=['classes="$tmpdir/classes"', 'mkdir -p "$classes"'],
        basename="Main",
        append_args=False,
    )


def _java_android_builder() -> Callable[[str, List[str]], str]:
    """Create builder for Android Java with dalvikvm support."""
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


# ---------- Language Registry ----------
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


# ---------- Language Processing Functions ----------
def _parse_polyglot_template(template: str) -> Optional[str]:
    """Parse polyglot template to extract language hint."""
    stripped = template.strip()
    m = re.match(
        r"^(?:lang|language|polyglot)\s*(?:[:=]|\s+)\s*(.+)$", stripped, re.IGNORECASE
    )
    if not m:
        return None
    return m.group(1).strip().lower()


def _canonical_lang(lang_hint: str) -> str:
    """Convert language hint to canonical language name."""
    lang_key = lang_hint.strip().lower()
    return POLYGLOT_ALIASES.get(lang_key, lang_key)


def _extract_polyglot_source(cmd: str, base_dir: Optional[str]) -> Tuple[str, List[str], Optional[str]]:
    """Extract polyglot source code from command."""
    tokens = shlex.split(cmd)
    if not tokens:
        return cmd, [], None
    
    if tokens[0].startswith("@") or tokens[0].startswith("file:"):
        if not base_dir:
            raise PFSyntaxError(
                message="Cannot resolve polyglot source file: no base directory available",
                suggestion="Ensure the Pfyfile is in a valid directory"
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


def render_polyglot_command(
    lang_hint: Optional[str], cmd: str, working_dir: Optional[str]
) -> Tuple[Optional[str], Optional[str]]:
    """Render polyglot command for execution."""
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


def get_supported_languages() -> List[str]:
    """Get list of all supported languages."""
    return sorted(POLYGLOT_LANGS.keys())


def get_language_aliases() -> Dict[str, str]:
    """Get mapping of language aliases to canonical names."""
    return POLYGLOT_ALIASES.copy()


def is_supported_language(lang_hint: str) -> bool:
    """Check if a language hint is supported."""
    lang_key = _canonical_lang(lang_hint)
    return lang_key in POLYGLOT_LANGS