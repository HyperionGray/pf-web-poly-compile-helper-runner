"""
Polyglot language support addon for pf-runner.

This addon handles execution of code in multiple programming languages,
extracting the polyglot functionality from the core parser.
"""

import shlex
from typing import Any, Dict, List, Tuple, Optional, Callable

from .interface import AddonInterface


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


class PolyglotAddon(AddonInterface):
    """Addon for executing code in multiple programming languages."""
    
    def __init__(self):
        # Language profiles - maps language names to code generators
        self._languages: Dict[str, Callable[[str, List[str]], str]] = {
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
        }
        
        # Language aliases
        self._aliases = {
            "shell": "bash",
            "python3": "python",
            "py": "python",
            "js": "node",
            "javascript": "node",
            "ts": "deno",
            "typescript": "deno",
            "c++": "cpp",
            "cxx": "cpp",
            "golang": "go",
            "rb": "ruby",
        }
    
    @property
    def name(self) -> str:
        return "polyglot"
    
    @property
    def version(self) -> str:
        return "1.0.0"
    
    def can_handle(self, operation: str, args: Dict[str, Any]) -> bool:
        """Check if this is a polyglot shell command."""
        return operation == "polyglot_shell" or (operation == "shell" and "lang" in args)
    
    def execute(self, operation: str, args: Dict[str, Any], context: Dict[str, Any]) -> str:
        """
        Execute polyglot code.
        
        Args:
            operation: Should be 'polyglot_shell'
            args: Must contain 'lang' and 'code', optionally 'args'
            context: Execution context
            
        Returns:
            The shell command to execute the code
        """
        lang = args.get('lang', 'bash')
        code = args.get('code', '')
        code_args = args.get('args', [])
        
        # Resolve aliases
        lang_key = self._aliases.get(lang.lower(), lang.lower())
        
        if lang_key not in self._languages:
            raise ValueError(f"Unsupported language: {lang}")
        
        builder = self._languages[lang_key]
        return builder(code, code_args)
    
    def validate(self, operation: str, args: Dict[str, Any]) -> Optional[str]:
        """Validate polyglot arguments."""
        if 'code' not in args:
            return "Missing required argument: code"
        
        lang = args.get('lang', 'bash')
        lang_key = self._aliases.get(lang.lower(), lang.lower())
        
        if lang_key not in self._languages:
            return f"Unsupported language: {lang}"
        
        return None
