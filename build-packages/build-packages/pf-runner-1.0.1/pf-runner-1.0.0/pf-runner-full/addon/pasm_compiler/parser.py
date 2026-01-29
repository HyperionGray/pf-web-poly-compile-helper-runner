"""Ultra-lightweight parser for the MLIR text emitted by clang+mlir-opt."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional

_ASSIGN_RE = re.compile(r"^\s*(%[\w\.]+)\s*=\s*([\w\.]+)\s*(.*)$")
_OP_RE = re.compile(r"^\s*([\w\.]+)\s+(.*)$")
_CONST_RE = re.compile(r"^\s*([^:]+?)\s*:\s*(.+?)\s*$")
_READ_RE = re.compile(r"^(%[\w\.]+)\[(%[\w\.]+)\]\s*:\s*([^,]+),\s*(\S+)\s*$")
_WRITE_RE = re.compile(
    r"^(%[\w\.]+),\s+(%[\w\.]+)\[(%[\w\.]+)\]\s*:\s*(\S+),\s*(\S+)\s*$"
)
_REDUCTION_RE = re.compile(r"vector\.reduction\s+\"(add|xor)\"")


@dataclass
class MlirOperation:
    result: Optional[str]
    op_name: str
    text: str


class MlirParseError(RuntimeError):
    pass


def parse_mlir(lines: Iterable[str]) -> List[MlirOperation]:
    ops: List[MlirOperation] = []
    for raw in lines:
        line = raw.strip()
        if not line or line.startswith("//"):
            continue
        if (
            line.startswith("module")
            or line.startswith("func.func")
            or line.startswith("return")
            or line == "}"
        ):
            continue
        assign = _ASSIGN_RE.match(line)
        if assign:
            result, op_name, rest = assign.groups()
            ops.append(MlirOperation(result=result, op_name=op_name, text=rest.strip()))
            continue
        op_match = _OP_RE.match(line)
        if op_match:
            op_name, rest = op_match.groups()
            ops.append(MlirOperation(result=None, op_name=op_name, text=rest.strip()))
            continue
    return ops


def extract_constant(op: MlirOperation) -> Optional[int]:
    if op.op_name != "arith.constant" or not op.result:
        return None
    m = _CONST_RE.search(op.text)
    if not m:
        raise MlirParseError(f"Unsupported constant form: {op.text}")
    literal, _type = m.groups()
    literal = literal.strip()
    if literal.startswith("-"):
        return int(literal)
    if literal.startswith("0x"):
        return int(literal, 16)
    return int(literal)


def extract_transfer_read(op: MlirOperation, constants: Dict[str, int]):
    m = _READ_RE.search(op.text)
    if not m:
        raise MlirParseError(f"Unsupported transfer_read: {op.text}")
    buffer_name, offset_sym, memref_ty, vec_ty = m.groups()
    offset = constants.get(offset_sym, 0)
    return {
        "buffer": buffer_name,
        "offset": offset,
        "memref_type": memref_ty.strip(),
        "vector_type": vec_ty.strip(),
    }


def extract_transfer_write(op: MlirOperation, constants: Dict[str, int]):
    m = _WRITE_RE.search(op.text)
    if not m:
        raise MlirParseError(f"Unsupported transfer_write: {op.text}")
    vec_name, buffer_name, offset_sym, vec_ty, memref_ty = m.groups()
    offset = constants.get(offset_sym, 0)
    return {
        "vector": vec_name,
        "buffer": buffer_name,
        "offset": offset,
        "vector_type": vec_ty.strip(),
        "memref_type": memref_ty.strip(),
    }


def extract_vector_reduction(op: MlirOperation):
    m = _REDUCTION_RE.search(op.text)
    if not m:
        raise MlirParseError(f"Unsupported vector.reduction form: {op.text}")
    kind = m.group(1)
    return kind
