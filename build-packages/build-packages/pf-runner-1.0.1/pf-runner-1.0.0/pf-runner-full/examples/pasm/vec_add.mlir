module {
  func.func @vec_add(%src0: memref<?xi64>, %src1: memref<?xi64>, %dst: memref<?xi64>) {
    %c0 = arith.constant 0 : index
    %v0 = vector.transfer_read %src0[%c0] : memref<?xi64>, vector<64xi64>
    %v1 = vector.transfer_read %src1[%c0] : memref<?xi64>, vector<64xi64>
    %v2 = arith.addi %v0, %v1 : vector<64xi64>
    vector.transfer_write %v2, %dst[%c0] : vector<64xi64>, memref<?xi64>
    return
  }
}
