"""Emit lowered programs as textual pASM plus JSON metadata."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from .dialect import PasmProgram


def emit_program(
    program: PasmProgram,
    text_path: Optional[Path] = None,
    json_path: Optional[Path] = None,
) -> None:
    text = _format_text(program)
    manifest = {
        "registers": [reg.name for reg in program.registers],
        "instructions": [
            {
                "opcode": inst.opcode,
                "dst": inst.dst.name if inst.dst else None,
                "srcs": [src.name for src in inst.srcs],
                "metadata": inst.metadata,
            }
            for inst in program.instructions
        ],
    }

    if text_path:
        Path(text_path).write_text(text, encoding="utf-8")
    if json_path:
        Path(json_path).write_text(json.dumps(manifest, indent=2), encoding="utf-8")


def _format_text(program: PasmProgram) -> str:
    lines = ["; pASM (lowered from MLIR)"]
    lines.append(f"; registers: {', '.join(reg.name for reg in program.registers)}")
    for inst in program.instructions:
        lines.append(inst.to_text())
    lines.append("")
    return "\n".join(lines)
