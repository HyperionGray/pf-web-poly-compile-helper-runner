#!/usr/bin/env bash
# Native installer smoke test (container path deprecated).

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

log_info() { printf '[INFO] %s\n' "$*"; }
log_ok()   { printf '[ OK ] %s\n' "$*"; }
log_err()  { printf '[ERR ] %s\n' "$*" >&2; }

run_native_install() {
  local workdir
  workdir="$(mktemp -d /tmp/pf-native-test-XXXX)"
  trap 'rm -rf "$workdir"' EXIT

  log_info "Copying repo to ${workdir}"
  cp -R "${SCRIPT_DIR}/." "${workdir}/repo"
  cd "${workdir}/repo"

  local prefix="${workdir}/install"
  log_info "Running ./install.sh --prefix ${prefix} --skip-deps"
  ./install.sh --prefix "${prefix}" --skip-deps

  PATH="${prefix}/bin:$PATH"
  if pf --version >/dev/null 2>&1 && pf list >/dev/null 2>&1; then
    log_ok "pf runs from installed prefix"
  else
    log_err "pf failed to run after install"
    return 1
  fi

  log_ok "Native install smoke test succeeded"
}

run_native_install
