#!/usr/bin/env python3
"""
pf_block_converter.py - Convert shell commands into shell_lang BLOCK sections.
"""

import argparse
import re
import sys
from typing import List, Optional, Tuple

from pf_exceptions import PFSyntaxError


_LANG_BRACKET_RE = re.compile(r"^\s*\[lang:([^\]]+)\]\s*(.*)$", re.IGNORECASE | re.DOTALL)
_SHELL_LANG_BLOCK_RE = re.compile(r"^shell_lang\s+(.+?)\s+BLOCK(?:\s+#.*)?$", re.IGNORECASE)
_SHELL_LANG_BLOCK_END_RE = re.compile(r"^ENDBLOCK(?:\s+#.*)?$", re.IGNORECASE)
_SHELL_HEREDOC_START_RE = re.compile(r"<<-?\s*(['\"]?)([A-Za-z][A-Za-z0-9_]*)\1")


KNOWN_VERBS = {
    "describe",
    "synopsis",
    "category",
    "example",
    "prerequisite",
    "troubleshooting",
    "see-also",
    "use-case",
    "note",
    "tag",
    "env",
    "shell",
    "shell_lang",
    "packages",
    "service",
    "directory",
    "copy",
    "sync",
    "if",
    "else",
    "for",
    "makefile",
    "make",
    "cmake",
    "meson",
    "ninja",
    "cargo",
    "go_build",
    "gobuild",
    "configure",
    "justfile",
    "just",
    "autobuild",
    "auto_build",
    "build_detect",
    "detect_build",
}


class _ShellBlockBuffer:
    def __init__(self, lang: str, indent: str):
        self.lang = lang
        self.indent = indent
        self.lines: List[str] = []

    def add(self, line: str) -> None:
        self.lines.append(line)


def _split_indent(line: str) -> Tuple[str, str]:
    indent_len = len(line) - len(line.lstrip(" "))
    return line[:indent_len], line[indent_len:]


def _is_shell_lang_block_header(line: str) -> Optional[str]:
    match = _SHELL_LANG_BLOCK_RE.match(line)
    if not match:
        return None
    lang = match.group(1).strip()
    if not lang:
        raise PFSyntaxError(
            message="shell_lang BLOCK requires a language name",
            suggestion="Use syntax: shell_lang bash BLOCK",
        )
    if lang.lower() in {"default", "none"}:
        raise PFSyntaxError(
            message="shell_lang BLOCK requires an explicit language",
            suggestion="Use syntax: shell_lang bash BLOCK",
        )
    return lang


def convert_shell_blocks(text: str, default_lang: str = "bash") -> str:
    """Convert shell commands in a pf file to shell_lang BLOCK sections."""
    lines = text.splitlines()
    out: List[str] = []

    stack: List[str] = []
    current_lang = default_lang
    buffer: Optional[_ShellBlockBuffer] = None

    in_shell_pipe_block = False
    shell_pipe_indent = 0
    in_shell_lang_block = False
    shell_lang_block_indent = 0
    pending_heredoc_delim: Optional[str] = None

    def flush_buffer() -> None:
        nonlocal buffer
        if not buffer:
            return
        out.append(f"{buffer.indent}shell_lang {buffer.lang} BLOCK")
        for line in buffer.lines:
            out.append(f"{buffer.indent}{line}" if line else buffer.indent)
        out.append(f"{buffer.indent}ENDBLOCK")
        buffer = None

    i = 0
    while i < len(lines):
        raw = lines[i]
        stripped = raw.strip()
        indent, content = _split_indent(raw)

        if pending_heredoc_delim is not None:
            out.append(raw)
            if stripped == pending_heredoc_delim:
                pending_heredoc_delim = None
            i += 1
            continue

        if in_shell_lang_block:
            out.append(raw)
            if _SHELL_LANG_BLOCK_END_RE.match(stripped) and len(indent) == shell_lang_block_indent:
                in_shell_lang_block = False
            i += 1
            continue

        if in_shell_pipe_block:
            out.append(raw)
            if stripped == "|" and len(indent) == shell_pipe_indent:
                in_shell_pipe_block = False
            elif stripped == "end":
                in_shell_pipe_block = False
            i += 1
            continue

        # Outside any task
        if not stack:
            if stripped.startswith("task "):
                flush_buffer()
                stack.append("task")
                current_lang = default_lang
            out.append(raw)
            i += 1
            continue

        # Inside a task (and not in passthrough blocks)
        if not stripped or stripped.startswith("#"):
            flush_buffer()
            out.append(raw)
            i += 1
            continue

        if _is_shell_lang_block_header(stripped):
            flush_buffer()
            in_shell_lang_block = True
            shell_lang_block_indent = len(indent)
            out.append(raw)
            i += 1
            continue

        if stripped == "shell |":
            flush_buffer()
            in_shell_pipe_block = True
            shell_pipe_indent = len(indent)
            out.append(raw)
            i += 1
            continue

        if stripped.startswith("task "):
            flush_buffer()
            stack.append("task")
            current_lang = default_lang
            out.append(raw)
            i += 1
            continue

        if stripped.startswith("if "):
            flush_buffer()
            stack.append("if")
            out.append(raw)
            i += 1
            continue

        if stripped.startswith("for "):
            flush_buffer()
            stack.append("for")
            out.append(raw)
            i += 1
            continue

        if stripped == "else":
            flush_buffer()
            out.append(raw)
            i += 1
            continue

        if stripped == "end":
            flush_buffer()
            if stack:
                stack.pop()
            out.append(raw)
            i += 1
            continue

        if stripped.startswith("shell_lang ") and not stripped.endswith("BLOCK"):
            flush_buffer()
            lang = stripped[len("shell_lang") :].strip()
            if lang and lang.lower() not in {"default", "none"}:
                current_lang = lang
            else:
                current_lang = default_lang
            out.append(raw)
            i += 1
            continue

        # Determine if this is a shell command (explicit or implicit)
        first_token = stripped.split(None, 1)[0] if stripped else ""
        is_shell_cmd = first_token == "shell" or first_token not in KNOWN_VERBS

        if not is_shell_cmd:
            flush_buffer()
            out.append(raw)
            i += 1
            continue

        # Check for heredoc start; pass through unmodified if found
        heredoc_match = _SHELL_HEREDOC_START_RE.search(stripped)
        if heredoc_match:
            flush_buffer()
            pending_heredoc_delim = heredoc_match.group(2)
            out.append(raw)
            i += 1
            continue

        # Normalize shell command content
        line_lang = current_lang
        shell_content = content.lstrip()
        if shell_content.startswith("shell "):
            shell_content = shell_content[6:].lstrip()

        lang_match = _LANG_BRACKET_RE.match(shell_content)
        if lang_match:
            line_lang = lang_match.group(1).strip()
            shell_content = lang_match.group(2)

        if buffer is None or buffer.lang != line_lang or buffer.indent != indent:
            flush_buffer()
            buffer = _ShellBlockBuffer(line_lang, indent)

        buffer.add(shell_content.rstrip("\n"))
        i += 1

    if pending_heredoc_delim is not None:
        raise PFSyntaxError(
            message=f"Unclosed heredoc: missing terminator '{pending_heredoc_delim}'",
            suggestion=f"Add a line containing only {pending_heredoc_delim} to close the heredoc",
        )

    if in_shell_lang_block:
        raise PFSyntaxError(
            message="Unclosed shell_lang BLOCK: missing ENDBLOCK",
            suggestion="Add a line containing only ENDBLOCK to close the block",
        )

    flush_buffer()
    return "\n".join(out) + ("\n" if text.endswith("\n") else "")


def _parse_args(argv: List[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="pf-block-convert",
        description="Convert shell commands to shell_lang BLOCK sections",
    )
    parser.add_argument(
        "file",
        nargs="?",
        default="-",
        help="Input file path (default: stdin)",
    )
    parser.add_argument(
        "--lang",
        default="bash",
        help="Default language for shell blocks (default: bash)",
    )
    parser.add_argument(
        "-o",
        "--output",
        help="Write output to file instead of stdout",
    )
    parser.add_argument(
        "--in-place",
        action="store_true",
        help="Overwrite the input file in place",
    )
    return parser.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> int:
    args = _parse_args(argv or sys.argv[1:])

    if args.in_place and (args.file == "-" or not args.file):
        print("--in-place requires a file path", file=sys.stderr)
        return 2

    if args.file == "-":
        source = sys.stdin.read()
    else:
        with open(args.file, "r", encoding="utf-8") as fh:
            source = fh.read()

    try:
        converted = convert_shell_blocks(source, default_lang=args.lang)
    except PFSyntaxError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        if exc.suggestion:
            print(f"Hint: {exc.suggestion}", file=sys.stderr)
        return 1

    if args.in_place:
        with open(args.file, "w", encoding="utf-8") as fh:
            fh.write(converted)
        return 0

    if args.output:
        with open(args.output, "w", encoding="utf-8") as fh:
            fh.write(converted)
        return 0

    sys.stdout.write(converted)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
