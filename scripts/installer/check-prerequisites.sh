#!/usr/bin/env bash
set -euo pipefail

PROFILE="${1:-core}"

usage() {
  cat <<'EOF'
Usage: check-prerequisites.sh [profile]

Profiles:
  core     Required tooling for pf installation and basic usage (default)
  web      Core + web workflow prerequisites
  exploit  Core + exploit workflow prerequisites
  debug    Core + debugging workflow prerequisites
  fuzzing  Core + fuzzing workflow prerequisites
  all      Core + all optional profiles
EOF
}

if [[ "${PROFILE}" == "-h" || "${PROFILE}" == "--help" ]]; then
  usage
  exit 0
fi

case "${PROFILE}" in
  core|web|exploit|debug|fuzzing|all) ;;
  *)
    echo "[ERR] Unknown profile: ${PROFILE}" >&2
    usage >&2
    exit 2
    ;;
esac

detect_platform() {
  if command -v apt-get >/dev/null 2>&1; then
    echo "debian"
    return
  fi
  if command -v dnf >/dev/null 2>&1; then
    echo "dnf"
    return
  fi
  if command -v yum >/dev/null 2>&1; then
    echo "yum"
    return
  fi
  if command -v pacman >/dev/null 2>&1; then
    echo "pacman"
    return
  fi
  if command -v zypper >/dev/null 2>&1; then
    echo "zypper"
    return
  fi
  if command -v apk >/dev/null 2>&1; then
    echo "apk"
    return
  fi
  if command -v brew >/dev/null 2>&1; then
    echo "brew"
    return
  fi
  echo "unknown"
}

install_hint() {
  local cmd="$1"
  local platform="$2"

  case "${platform}" in
    debian)
      case "${cmd}" in
        python3) echo "sudo apt-get install -y python3 python3-pip" ;;
        git) echo "sudo apt-get install -y git" ;;
        curl) echo "sudo apt-get install -y curl" ;;
        node|npm|npx) echo "sudo apt-get install -y nodejs npm" ;;
        gdb) echo "sudo apt-get install -y gdb" ;;
        lldb) echo "sudo apt-get install -y lldb" ;;
        clang) echo "sudo apt-get install -y clang" ;;
        afl-fuzz) echo "sudo apt-get install -y afl++" ;;
        checksec) echo "pf install-checksec" ;;
        ROPgadget) echo "pf install-ropgadget" ;;
        ropper) echo "pf install-ropper" ;;
        *) echo "Install ${cmd} with your package manager" ;;
      esac
      ;;
    dnf|yum)
      echo "Install ${cmd} with ${platform}"
      ;;
    pacman)
      echo "sudo pacman -S ${cmd}"
      ;;
    zypper)
      echo "sudo zypper install ${cmd}"
      ;;
    apk)
      echo "sudo apk add ${cmd}"
      ;;
    brew)
      echo "brew install ${cmd}"
      ;;
    *)
      echo "Install ${cmd} manually for your platform"
      ;;
  esac
}

PLATFORM="$(detect_platform)"
missing_required=0
missing_optional=0

echo "Installer prerequisite check"
echo "Profile : ${PROFILE}"
echo "Platform: ${PLATFORM}"
echo ""

check_required() {
  local cmd="$1"
  local desc="$2"
  if command -v "${cmd}" >/dev/null 2>&1; then
    echo "[OK] ${cmd} - ${desc}"
  else
    echo "[MISSING] ${cmd} - ${desc}"
    echo "          Hint: $(install_hint "${cmd}" "${PLATFORM}")"
    missing_required=$((missing_required + 1))
  fi
}

check_optional() {
  local cmd="$1"
  local desc="$2"
  if command -v "${cmd}" >/dev/null 2>&1; then
    echo "[OK] ${cmd} - ${desc}"
  else
    echo "[OPTIONAL] ${cmd} - ${desc}"
    echo "          Hint: $(install_hint "${cmd}" "${PLATFORM}")"
    missing_optional=$((missing_optional + 1))
  fi
}

echo "Core requirements:"
check_required "python3" "required to run pf and helper scripts"
check_required "git" "required for repository workflows and some installers"
check_required "curl" "required by several installer tasks"
echo ""

echo "Core optional helpers:"
check_optional "pip3" "recommended for Python package-based tooling"
check_optional "node" "required for web/dev workflows"
check_optional "npm" "required for JS-based tooling and tests"
echo ""

if [[ "${PROFILE}" == "web" || "${PROFILE}" == "all" ]]; then
  echo "Web profile checks:"
  check_optional "node" "web server and frontend tooling"
  check_optional "npm" "dependency management for web tooling"
  check_optional "npx" "Playwright and local CLI helpers"
  echo ""
fi

if [[ "${PROFILE}" == "exploit" || "${PROFILE}" == "all" ]]; then
  echo "Exploit profile checks:"
  check_optional "checksec" "binary hardening analysis"
  check_optional "ROPgadget" "ROP gadget discovery"
  check_optional "ropper" "ROP chain support"
  echo ""
fi

if [[ "${PROFILE}" == "debug" || "${PROFILE}" == "all" ]]; then
  echo "Debug profile checks:"
  check_optional "gdb" "GNU debugger"
  check_optional "lldb" "LLVM debugger"
  echo ""
fi

if [[ "${PROFILE}" == "fuzzing" || "${PROFILE}" == "all" ]]; then
  echo "Fuzzing profile checks:"
  check_optional "clang" "compiler used by sanitizer and fuzzing tasks"
  check_optional "afl-fuzz" "AFL++ fuzzer runtime"
  echo ""
fi

echo "Summary:"
echo "  Missing required: ${missing_required}"
echo "  Missing optional: ${missing_optional}"
echo ""

if [[ "${missing_required}" -gt 0 ]]; then
  echo "[ERR] Required prerequisites are missing."
  echo "Run this check again after installing prerequisites."
  exit 1
fi

echo "[OK] Required prerequisites are available."
echo "Next steps:"
echo "  pf install"
echo "  pf install-verify profile=${PROFILE}"
exit 0
