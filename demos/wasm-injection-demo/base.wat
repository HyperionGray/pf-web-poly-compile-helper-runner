(module
  (func $original (param $x i32) (result i32)
    local.get $x
    i32.const 10
    i32.mul)
  (export "calculate" (func $original))
)
