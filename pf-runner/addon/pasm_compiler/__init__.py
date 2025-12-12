"""Minimal MLIR → pASM lowering helpers for pf-runner."""

from .dialect import PasmInstruction, PasmProgram  # noqa: F401
from .lowering import lower_mlir_to_pasm  # noqa: F401
from .emit import emit_program  # noqa: F401
