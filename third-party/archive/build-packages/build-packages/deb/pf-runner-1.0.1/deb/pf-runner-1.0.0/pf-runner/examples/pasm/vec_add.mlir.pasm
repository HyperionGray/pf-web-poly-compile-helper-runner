; pASM (lowered from MLIR)
; registers: v0, v1, v2
PASM_VGATHER v0 ; buffer=%src0 offset=0 vector_type=vector<64xi64>
PASM_VGATHER v1 ; buffer=%src1 offset=0 vector_type=vector<64xi64>
PASM_VADD v2 v0, v1
PASM_VSCATTER - v2 ; buffer=%dst offset=0 vector_type=vector<64xi64>
PASM_HALT
