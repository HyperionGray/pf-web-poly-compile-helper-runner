#!/usr/bin/env python3
"""
pf_dsl_parser.py - Core pf DSL parsing helpers.

This module isolates the grammar-ish parsing logic from pf_parser.py so the
rest of the runner can evolve without wading through parsing details.
"""

import re
import shlex
from typing import Dict, List, Optional, Tuple

try:
    from pf_exceptions import PFSyntaxError
except ImportError:
    class PFSyntaxError(Exception):
        pass


class Task:
    def __init__(
        self,
        name: str,
        source_file: Optional[str] = None,
        params: Optional[Dict[str, str]] = None,
        aliases: Optional[List[str]] = None,
        rc: bool = False,
    ):
        self.name = name
        self.lines: List[str] = []
        self.description: Optional[str] = None
        self.source_file = source_file  # Track which file this task came from
        self.params: Dict[str, str] = params or {}  # Default parameter values
        self.aliases: List[str] = aliases or []  # Command aliases for this task
        self.rc: bool = bool(rc)  # Export as a shell alias via ~/.bashrc (opt-in)

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
        self.param_help: Dict[str, str] = {}  # Param descriptions keyed by name

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

    def add_param_help(self, param: str, description: str):
        """Add a description for a task parameter."""
        if param:
            self.param_help[param] = description


_ALIAS_BLOCK_RE = re.compile(r"\[([^\]]+)\]")


def _parse_task_definition_with_meta(line: str) -> Tuple[str, Dict[str, str], List[str], bool]:
    """
    Parse a task definition line to extract task name, parameters, and aliases.
    Also supports `rc=true` metadata to opt into shell alias export.

    Examples:
        "task my-task" -> ("my-task", {}, [], False)
        "task my-task param1=value1" -> ("my-task", {"param1": "value1"}, [], False)
        "task my-task rc=true" -> ("my-task", {}, [], True)
        "task my-task param1=\"\" param2=default" -> ("my-task", {"param1": "", "param2": "default"}, [], False)
        "task long-command [alias cmd]" -> ("long-command", {}, ["cmd"], False)
        "task long-command [alias=cmd]" -> ("long-command", {}, ["cmd"], False)
        "task long-command [alias cmd|alias=c]" -> ("long-command", {}, ["cmd", "c"], False)

    Returns:
        Tuple of (task_name, parameters_dict, aliases_list, rc_enabled)
    """
    # Remove "task " prefix
    rest = line[5:].strip()
    if not rest:
        raise PFSyntaxError(
            message="Task name missing",
            suggestion="Task definition format: task task-name [param=\"value\"]",
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
            suggestion="Check for unclosed quotes or invalid escape sequences",
        )

    if not tokens:
        raise PFSyntaxError(
            message="Task name missing after parsing",
            suggestion="Task definition format: task task-name [param=\"value\"]",
        )

    task_name = tokens[0]
    params: Dict[str, str] = {}
    rc_enabled = False

    # Parse parameter definitions (key=value pairs)
    for token in tokens[1:]:
        if "=" in token:
            key, value = token.split("=", 1)
            if key == "rc":
                rc_enabled = str(value).strip().lower() in {"1", "true", "yes", "on"}
                continue
            params[key] = value
        else:
            # If a token doesn't have '=', it might be part of task name (shouldn't happen with proper syntax)
            # For now, we'll just skip it to be lenient
            pass

    return task_name, params, aliases, rc_enabled


def _parse_task_definition(line: str) -> Tuple[str, Dict[str, str], List[str]]:
    """
    Backward-compatible wrapper (legacy callers/tests expect 3-tuple).

    Prefer `_parse_task_definition_with_meta()` when you need task metadata like `rc=true`.
    """
    name, params, aliases, _ = _parse_task_definition_with_meta(line)
    return name, params, aliases


def _process_line_continuation(lines: List[str], start_idx: int) -> Tuple[str, int]:
    """
    Process bash-style backslash line continuation starting from the given index.

    Continuations are joined with a single space and leading indentation is removed
    from each physical line. This turns:

      shell echo "a" \\
            && echo "b"

    into a single logical line:

      shell echo "a" && echo "b"

    Returns:
        (combined_line, next_index_to_process)
    """
    combined_parts: List[str] = []
    i = start_idx

    while i < len(lines):
        raw = lines[i].rstrip("\n")
        stripped = raw.strip()

        # Skip empty lines and comments during continuation
        if not stripped or stripped.startswith("#"):
            i += 1
            continue

        has_backslash = stripped.endswith("\\")
        if has_backslash:
            stripped = stripped[:-1].rstrip()

        if stripped:
            combined_parts.append(stripped)

        i += 1
        if not has_backslash:
            break

    return " ".join(combined_parts).strip(), i


_SHELL_HEREDOC_START_RE = re.compile(r"<<-?\s*(['\"]?)([A-Za-z][A-Za-z0-9_]*)\1")


def _extract_heredoc_delimiter(shell_stmt: str) -> Optional[str]:
    """
    Best-effort heredoc delimiter extraction for shell statements like:
      shell cat << EOF
      shell cat << 'EOF'
      shell cat <<-EOF
    """
    m = _SHELL_HEREDOC_START_RE.search(shell_stmt)
    if not m:
        return None
    return m.group(2)


def _consume_shell_heredoc(lines: List[str], start_idx: int, first_line: str, delimiter: str) -> Tuple[str, int]:
    """
    Consume a shell heredoc starting at `start_idx` (the line containing the heredoc opener).

    Returns:
        (combined_shell_command, next_index_to_process)

    The combined command preserves heredoc content lines exactly as written.
    """
    parts: List[str] = [first_line.rstrip("\n")]
    i = start_idx + 1

    while i < len(lines):
        raw = lines[i].rstrip("\n")
        parts.append(raw)
        i += 1
        if raw.strip() == delimiter:
            return "\n".join(parts), i

    raise PFSyntaxError(
        message=f"Unclosed heredoc: missing terminator '{delimiter}'",
        suggestion=f"Add a line containing only {delimiter} to close the heredoc",
        line_number=start_idx + 1,
    )


_SHELL_LANG_BLOCK_RE = re.compile(
    r"^shell_lang\s+(.+?)\s+BLOCK(?:\s+#.*)?$", re.IGNORECASE
)
_SHELL_LANG_BLOCK_END_RE = re.compile(r"^ENDBLOCK(?:\s+#.*)?$", re.IGNORECASE)


def _parse_shell_lang_block_header(line: str) -> Optional[str]:
    """
    Parse a shell_lang BLOCK header like:
      shell_lang python BLOCK
      shell_lang bash BLOCK # comment

    Returns the language name or None if not a block header.
    """
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


def _consume_shell_lang_block(
    lines: List[str],
    start_idx: int,
    shell_indent: int,
    lang: str,
) -> Tuple[str, int]:
    """
    Consume a `shell_lang <lang> BLOCK` block inside a task.

    The block ends at an `ENDBLOCK` line aligned with the header indentation.
    """
    i = start_idx + 1
    block_raw: List[str] = []

    closed = False
    while i < len(lines):
        raw = lines[i].rstrip("\n")
        stripped = raw.strip()
        indent = len(raw) - len(raw.lstrip(" "))

        if _SHELL_LANG_BLOCK_END_RE.match(stripped):
            if indent == shell_indent:
                closed = True
                i += 1
                break

        block_raw.append(raw)
        i += 1

    if not closed:
        raise PFSyntaxError(
            message="Unclosed shell_lang BLOCK: missing ENDBLOCK",
            suggestion="Add a line containing only ENDBLOCK to close the block",
            line_number=start_idx + 1,
        )

    # Dedent based on the first non-empty line to preserve indentation-sensitive code.
    base_dedent = 0
    for raw in block_raw:
        if raw.strip():
            base_dedent = len(raw) - len(raw.lstrip(" "))
            break

    dedented: List[str] = []
    for raw in block_raw:
        if not raw.strip():
            dedented.append("")
            continue
        leading = len(raw) - len(raw.lstrip(" "))
        if base_dedent and leading >= base_dedent:
            dedented.append(raw[base_dedent:])
        else:
            dedented.append(raw)

    code = "\n".join(dedented)
    combined = f"shell [lang:{lang}] {code}".rstrip()
    return combined, i


def _consume_shell_pipe_block(lines: List[str], start_idx: int, shell_indent: int) -> Tuple[str, int]:
    """
    Consume a `shell |` literal block inside a task.

    The block ends either at an explicit `|` terminator line aligned with the
    `shell |` indentation, or at the task's `end` line.
    """
    i = start_idx + 1
    block_raw: List[str] = []

    while i < len(lines):
        raw = lines[i].rstrip("\n")
        stripped = raw.strip()

        # Explicit terminator line aligned with the `shell |` indentation
        if stripped == "|":
            indent = len(raw) - len(raw.lstrip(" "))
            if indent == shell_indent:
                i += 1
                break

        # Task end closes the block implicitly
        if stripped == "end":
            break

        block_raw.append(raw)
        i += 1

    # Dedent based on the first non-empty line to preserve heredoc bodies that
    # must remain unindented (e.g., `cat << 'EOF'` content).
    base_dedent = 0
    for raw in block_raw:
        if raw.strip():
            base_dedent = len(raw) - len(raw.lstrip(" "))
            break

    dedented: List[str] = []
    for raw in block_raw:
        if not raw.strip():
            dedented.append("")
            continue
        leading = len(raw) - len(raw.lstrip(" "))
        if base_dedent and leading >= base_dedent:
            dedented.append(raw[base_dedent:])
        else:
            dedented.append(raw)

    code = "\n".join(dedented)
    combined = f"shell {code}".rstrip()
    return combined, i


def parse_pfyfile_text(
    text: str, task_sources: Optional[Dict[str, str]] = None
) -> Dict[str, Task]:
    """Parse Pfyfile text into Task objects with optional source tracking.

    Supports bash-style backslash line continuation: lines ending with '\\'
    are joined with following lines until a line without trailing backslash.

    Args:
        text: The Pfyfile content to parse
        task_sources: Optional mapping of task names to source files

    Returns:
        Dictionary mapping task names to Task objects
    """
    tasks_dict: Dict[str, Task] = {}
    current_task: Optional[Task] = None
    lines = text.splitlines(keepends=True)
    i = 0

    while i < len(lines):
        raw = lines[i]
        stripped = raw.strip()

        # Skip empty lines and comments
        if not stripped or stripped.startswith("#"):
            i += 1
            continue

        # Parse task definition
        if stripped.startswith("task "):
            try:
                task_name, params, aliases, rc_enabled = _parse_task_definition_with_meta(stripped)
                source_file = task_sources.get(task_name) if task_sources else None
                current_task = Task(task_name, source_file, params, aliases, rc=rc_enabled)
                tasks_dict[task_name] = current_task
            except (ValueError, PFSyntaxError):
                current_task = None
            i += 1
            continue

        # End of task
        if stripped == "end":
            current_task = None
            i += 1
            continue

        # Ignore non-task lines at top level
        if current_task is None:
            i += 1
            continue

        # ----- Inside a task body -----
        # Handle `shell_lang <lang> BLOCK` blocks (must happen before continuation/heredoc handling).
        lang_block = _parse_shell_lang_block_header(stripped)
        if lang_block is not None:
            shell_indent = len(raw) - len(raw.lstrip(" "))
            combined, i = _consume_shell_lang_block(lines, i, shell_indent, lang_block)
            stripped = combined.strip()
            raw = combined
        # Handle `shell |` blocks (must happen before continuation/heredoc handling).
        elif stripped == "shell |":
            shell_indent = len(raw) - len(raw.lstrip(" "))
            combined, i = _consume_shell_pipe_block(lines, i, shell_indent)
            stripped = combined.strip()
            raw = combined
        else:
            # Handle backslash line continuation for normal single-line statements.
            if stripped.endswith("\\"):
                combined, i = _process_line_continuation(lines, i)
                stripped = combined.strip()
                raw = combined
            else:
                raw = stripped
                i += 1

            # Handle shell heredocs like:
            #   shell cat << 'EOF'
            #   [lang:python] << PYEOF
            #   cat << EOF
            #
            # Note: We intentionally detect heredocs even when the explicit `shell`
            # verb is omitted, to support the flexible syntax where plain lines are
            # treated as shell commands by default.
            delim = _extract_heredoc_delimiter(stripped)
            if delim:
                combined, i = _consume_shell_heredoc(lines, i - 1, stripped, delim)
                stripped = combined.strip()
                raw = combined

        # Metadata statements
        if stripped.startswith("describe "):
            current_task.description = stripped[9:].strip()
            continue
        if stripped.startswith("synopsis "):
            current_task.synopsis = stripped[9:].strip()
            continue
        if stripped.startswith("category "):
            current_task.category = stripped[9:].strip()
            continue
        if stripped.startswith("example "):
            current_task.add_example(stripped[8:].strip())
            continue
        if stripped.startswith("prerequisite "):
            current_task.add_prerequisite(stripped[13:].strip())
            continue
        if stripped.startswith("troubleshooting "):
            current_task.add_troubleshooting(stripped[16:].strip())
            continue
        if stripped.startswith("see-also "):
            current_task.add_see_also(stripped[9:].strip())
            continue
        if stripped.startswith("param-help "):
            payload = stripped[11:].strip()
            if payload:
                parts = payload.split(None, 1)
                param_name = parts[0]
                description = parts[1].strip() if len(parts) > 1 else ""
                current_task.add_param_help(param_name, description)
            continue
        if stripped.startswith("use-case "):
            current_task.add_use_case(stripped[9:].strip())
            continue
        if stripped.startswith("note "):
            current_task.add_note(stripped[5:].strip())
            continue
        if stripped.startswith("tag "):
            current_task.add_tag(stripped[4:].strip())
            continue

        # Store executable/task lines (verbatim, already de-indented).
        current_task.add(raw)

    if current_task is not None:
        raise PFSyntaxError(
            message=f"Unclosed task block: '{current_task.name}'",
            suggestion="Add 'end' to close the task block",
        )

    return tasks_dict
