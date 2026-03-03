#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
echo "Building target application..."
gcc -o target-app target-app.c
echo "Building C injection payload..."
gcc -shared -fPIC simple-payload.c -ldl -o simple-payload.so
echo "Building Fortran injection payload..."
gfortran -shared -fPIC fortran-payload.f90 fortran-wrapper.c -o fortran-payload.so
echo "Building Rust injection payload..."
pushd rust-payload >/dev/null
cargo build --release --target x86_64-unknown-linux-gnu
popd >/dev/null
cp rust-payload/target/x86_64-unknown-linux-gnu/release/librust_payload.so rust-payload.so 2>/dev/null || echo "Rust payload build may have failed"
echo "All injection examples built successfully!"
ls -lh *.so target-app 2>/dev/null || true
