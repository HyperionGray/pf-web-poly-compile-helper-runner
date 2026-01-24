"""In-memory representation of lowered pASM programs."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass(frozen=True)
class Register:
    name: str

    def __str__(self) -> str:  # pragma: no cover - trivial
        return self.name


@dataclass
class PasmInstruction:
    opcode: str
    dst: Optional[Register]
    srcs: List[Register] = field(default_factory=list)
    metadata: Dict[str, object] = field(default_factory=dict)

    def to_text(self) -> str:
        parts: List[str] = [self.opcode]
        if self.dst:
            parts.append(str(self.dst))
        if self.srcs:
            if not self.dst:
                parts.append("-")
            parts.append(", ".join(str(src) for src in self.srcs))
        if self.metadata:
            meta_blob = " ".join(
                f"{key}={value}" for key, value in sorted(self.metadata.items())
            )
            parts.append(f"; {meta_blob}")
        return " ".join(parts)


@dataclass
class PasmProgram:
    registers: List[Register]
    instructions: List[PasmInstruction]

    def summary(self) -> Dict[str, object]:
        return {
            "registers": [reg.name for reg in self.registers],
            "instruction_count": len(self.instructions),
            "opcodes": [inst.opcode for inst in self.instructions],
        }
