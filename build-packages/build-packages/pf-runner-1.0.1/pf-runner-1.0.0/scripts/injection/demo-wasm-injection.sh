#!/usr/bin/env bash
set -euo pipefail

echo "-- WASM Injection Workflow Demo --"
mkdir -p demos/wasm-injection-demo

echo "1. Creating base WASM module..."
cat > demos/wasm-injection-demo/base.wat <<'WAT_EOF'
(module
  (func $original (param $x i32) (result i32)
    local.get $x
    i32.const 10
    i32.mul)
  (export "calculate" (func $original))
)
WAT_EOF

if command -v wat2wasm >/dev/null 2>&1; then
  wat2wasm demos/wasm-injection-demo/base.wat -o demos/wasm-injection-demo/base.wasm
else
  echo "WABT (wat2wasm) not installed; skipping wasm compile"
fi

echo "2. Creating hook component..."
pf create-wasm-hook output=demos/wasm-injection-demo/hook.wat || true

echo "OK Demo files created in demos/wasm-injection-demo/"
ls -lh demos/wasm-injection-demo/
