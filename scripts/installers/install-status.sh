#!/usr/bin/env bash
set -euo pipefail

ok_count=0
missing_count=0

missing_exploit=0
missing_debug=0
missing_injection=0
missing_fuzzing=0
missing_package=0
missing_core=0

mark_ok() {
  ok_count=$((ok_count + 1))
}

mark_missing() {
  missing_count=$((missing_count + 1))
}

check_cmd() {
  local label="$1"
  local command_name="$2"
  local category="$3"
  if command -v "$command_name" >/dev/null 2>&1; then
    echo "  [OK] $label"
    mark_ok
  else
    echo "  [NO] $label"
    mark_missing
    case "$category" in
      core) missing_core=1 ;;
      exploit) missing_exploit=1 ;;
      debug) missing_debug=1 ;;
      injection) missing_injection=1 ;;
      fuzzing) missing_fuzzing=1 ;;
      package) missing_package=1 ;;
    esac
  fi
}

check_python_module() {
  local label="$1"
  local module_name="$2"
  local category="$3"
  if python3 -c "import ${module_name}" >/dev/null 2>&1; then
    echo "  [OK] $label"
    mark_ok
  else
    echo "  [NO] $label"
    mark_missing
    case "$category" in
      core) missing_core=1 ;;
      exploit) missing_exploit=1 ;;
      debug) missing_debug=1 ;;
      injection) missing_injection=1 ;;
      fuzzing) missing_fuzzing=1 ;;
      package) missing_package=1 ;;
    esac
  fi
}

echo "╔════════════════════════════════════════════════════════════╗"
echo "║                  PF INSTALL STATUS REPORT                 ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

echo "Core Runtime:"
check_cmd "pf command" "pf" "core"
check_cmd "python3" "python3" "core"
check_cmd "node" "node" "core"
echo ""

echo "Exploit Toolchain:"
check_python_module "pwntools (python module: pwn)" "pwn" "exploit"
check_cmd "checksec" "checksec" "exploit"
check_cmd "ROPgadget" "ROPgadget" "exploit"
check_cmd "ropper" "ropper" "exploit"
echo ""

echo "Debugging / RE Toolchain:"
check_cmd "oryx" "oryx" "debug"
check_cmd "binsider" "binsider" "debug"
check_cmd "radare2 (r2)" "r2" "debug"
check_cmd "snowman" "snowman" "debug"
check_cmd "rustnet" "rustnet" "debug"
check_cmd "sysz" "sysz" "debug"
check_cmd "gdb" "gdb" "debug"
check_cmd "lldb" "lldb" "debug"
echo ""

echo "Injection / Binary Utilities:"
check_cmd "patchelf" "patchelf" "injection"
check_cmd "nasm" "nasm" "injection"
check_cmd "wasm-opt (binaryen)" "wasm-opt" "injection"
check_cmd "wat2wasm (wabt)" "wat2wasm" "injection"
echo ""

echo "Fuzzing Toolchain:"
check_cmd "afl-fuzz" "afl-fuzz" "fuzzing"
check_cmd "clang" "clang" "fuzzing"
echo ""

echo "Package Management:"
check_cmd "dpkg (.deb)" "dpkg" "package"
check_cmd "rpm (.rpm)" "rpm" "package"
check_cmd "flatpak (.flatpak)" "flatpak" "package"
check_cmd "snap (.snap)" "snap" "package"
check_cmd "pacman (.pkg.tar.zst)" "pacman" "package"
echo ""

total=$((ok_count + missing_count))
if [ "$total" -eq 0 ]; then
  pct=0
else
  pct=$((ok_count * 100 / total))
fi

echo "Summary:"
echo "  [OK] Installed checks: $ok_count/$total (${pct}%)"
echo "  [NO] Missing checks:   $missing_count/$total"
echo ""

if [ "$missing_count" -eq 0 ]; then
  echo "All checked tools are available."
  exit 0
fi

echo "Recommended next steps:"
if [ "$missing_core" -eq 1 ]; then
  echo "  - Core runtime: pf install"
fi
if [ "$missing_exploit" -eq 1 ]; then
  echo "  - Exploit tools: pf install-exploit-tools"
fi
if [ "$missing_debug" -eq 1 ]; then
  echo "  - Debug tools: pf install-all-debug-tools"
fi
if [ "$missing_injection" -eq 1 ]; then
  echo "  - Injection tools: pf install-injection-tools"
fi
if [ "$missing_fuzzing" -eq 1 ]; then
  echo "  - Fuzzing tools: pf install-fuzzing-tools"
fi
if [ "$missing_package" -eq 1 ]; then
  echo "  - Package tools: pf install-pkg-tools (plus pf install-flatpak / pf install-snap as needed)"
fi
