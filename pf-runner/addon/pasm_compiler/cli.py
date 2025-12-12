"""Command-line entrypoint for the pf-runner MLIR → pASM compiler."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Optional

from .emit import emit_program
from .lowering import lower_mlir_to_pasm


def _default_output(input_path: Path, suffix: str) -> Path:
    return input_path.with_suffix(input_path.suffix + suffix)


def compile_file(
    mlir_path: Path,
    text_path: Optional[Path] = None,
    json_path: Optional[Path] = None,
    emit_summary: bool = False,
) -> None:
    mlir_text = mlir_path.read_text(encoding="utf-8")
    program = lower_mlir_to_pasm(mlir_text)
    if text_path is None:
        text_path = _default_output(mlir_path, ".pasm")
    if json_path is None:
        json_path = _default_output(mlir_path, ".manifest.json")
    emit_program(program, text_path=text_path, json_path=json_path)
    if emit_summary:
        print(json.dumps(program.summary(), indent=2))


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Compile MLIR vector kernels to pASM")
    parser.add_argument("mlir", type=Path, help="Path to MLIR input file")
    parser.add_argument("--text", type=Path, help="Textual pASM output path")
    parser.add_argument("--manifest", type=Path, help="JSON manifest output path")
    parser.add_argument("--summary", action="store_true", help="Print summary JSON")
    args = parser.parse_args(argv)

    compile_file(
        mlir_path=args.mlir,
        text_path=args.text,
        json_path=args.manifest,
        emit_summary=args.summary,
    )
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
