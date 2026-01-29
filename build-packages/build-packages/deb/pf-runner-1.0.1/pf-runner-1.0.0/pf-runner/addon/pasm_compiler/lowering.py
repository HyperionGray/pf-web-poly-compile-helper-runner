"""Lower a subset of MLIR vector/arith ops into pASM instructions."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

from .dialect import PasmInstruction, PasmProgram, Register
from .parser import (
    MlirOperation,
    MlirParseError,
    extract_constant,
    extract_transfer_read,
    extract_transfer_write,
    extract_vector_reduction,
    parse_mlir,
)


@dataclass
class _RegisterFile:
    next_id: int = 0
    values: Dict[str, Register] = None
    order: List[str] = None

    def __post_init__(self):
        if self.values is None:
            self.values = {}
        if self.order is None:
            self.order = []

    def allocate(self, value_name: str) -> Register:
        reg = Register(f"v{self.next_id}")
        self.next_id += 1
        self.values[value_name] = reg
        self.order.append(value_name)
        return reg

    def require(self, value_name: str) -> Register:
        if value_name not in self.values:
            raise MlirParseError(f"No register allocated for {value_name}")
        return self.values[value_name]

    def all_registers(self) -> List[Register]:
        return [self.values[key] for key in self.order]


def _parse_vector_operands(op: MlirOperation) -> List[str]:
    front = op.text.split(":", 1)[0]
    return [tok.strip() for tok in front.split(",") if tok.strip()]


def lower_mlir_to_pasm(mlir_text: str) -> PasmProgram:
    ops = parse_mlir(mlir_text.splitlines())
    consts: Dict[str, int] = {}
    reg_file = _RegisterFile()
    instructions: List[PasmInstruction] = []

    for op in ops:
        if op.op_name == "arith.constant":
            val = extract_constant(op)
            if val is not None and op.result:
                consts[op.result] = val
            continue

        if op.op_name == "vector.transfer_read":
            info = extract_transfer_read(op, consts)
            dst = reg_file.allocate(op.result or f"tmp{len(instructions)}")
            instructions.append(
                PasmInstruction(
                    opcode="PASM_VGATHER",
                    dst=dst,
                    metadata={
                        "buffer": info["buffer"],
                        "offset": info["offset"],
                        "vector_type": info["vector_type"],
                    },
                )
            )
            continue

        if op.op_name == "vector.transfer_write":
            info = extract_transfer_write(op, consts)
            vec_reg = reg_file.require(info["vector"])
            instructions.append(
                PasmInstruction(
                    opcode="PASM_VSCATTER",
                    dst=None,
                    srcs=[vec_reg],
                    metadata={
                        "buffer": info["buffer"],
                        "offset": info["offset"],
                        "vector_type": info["vector_type"],
                    },
                )
            )
            continue

        if op.op_name.startswith("arith.add"):
            operands = _parse_vector_operands(op)
            if len(operands) != 2:
                raise MlirParseError(f"Expected two operands for add, got: {op.text}")
            src0 = reg_file.require(operands[0])
            src1 = reg_file.require(operands[1])
            dst = reg_file.allocate(op.result or f"tmp{len(instructions)}")
            instructions.append(
                PasmInstruction(opcode="PASM_VADD", dst=dst, srcs=[src0, src1])
            )
            continue

        if op.op_name.startswith("arith.xor"):
            operands = _parse_vector_operands(op)
            if len(operands) != 2:
                raise MlirParseError(f"Expected two operands for xor, got: {op.text}")
            src0 = reg_file.require(operands[0])
            src1 = reg_file.require(operands[1])
            dst = reg_file.allocate(op.result or f"tmp{len(instructions)}")
            instructions.append(
                PasmInstruction(opcode="PASM_VXOR", dst=dst, srcs=[src0, src1])
            )
            continue

        if op.op_name == "vector.reduction":
            kind = extract_vector_reduction(op)
            opcode = {
                "add": "PASM_VREDUCE_ADD",
                "xor": "PASM_VREDUCE_XOR",
            }.get(kind)
            if not opcode:
                raise MlirParseError(f"Unsupported reduction kind: {kind}")
            operands = _parse_vector_operands(op)
            if len(operands) != 1:
                raise MlirParseError(f"Expected single operand for reduction: {op.text}")
            src = reg_file.require(operands[0])
            dst = reg_file.allocate(op.result or f"tmp{len(instructions)}")
            instructions.append(PasmInstruction(opcode=opcode, dst=dst, srcs=[src]))
            continue

        raise MlirParseError(f"Unsupported op: {op.op_name}")

    instructions.append(PasmInstruction(opcode="PASM_HALT", dst=None, srcs=[]))
    return PasmProgram(registers=reg_file.all_registers(), instructions=instructions)
