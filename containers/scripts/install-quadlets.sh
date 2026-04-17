#!/usr/bin/env bash
# install-quadlets.sh - install/remove/list/status helper for pf quadlet files
set -euo pipefail

log_info() { echo "INFO $*"; }
log_warn() { echo "WARN $*"; }
log_error() { echo "ERROR $*"; }

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
QUADLET_SRC="${PROJECT_ROOT}/containers/quadlets"
DEST_USER="${XDG_CONFIG_HOME:-${HOME}/.config}/containers/systemd"

SYSTEMCTL="systemctl --user"
if [[ ${EUID:-0} -eq 0 ]]; then
    SYSTEMCTL="systemctl"
fi

reload_systemd() {
    if command -v systemctl >/dev/null 2>&1; then
        ${SYSTEMCTL} daemon-reload >/dev/null 2>&1 || log_warn "systemd reload failed; reload manually if needed"
    else
        log_warn "systemctl not found; skipping daemon-reload"
    fi
}

install_quadlets() {
    if [[ ! -d "${QUADLET_SRC}" ]]; then
        log_error "Quadlet source directory not found: ${QUADLET_SRC}"
        exit 1
    fi

    mkdir -p "${DEST_USER}"
    cp -f "${QUADLET_SRC}"/pf-* "${DEST_USER}/"
    reload_systemd
    log_info "Installed pf quadlets to ${DEST_USER}"
}

remove_quadlets() {
    if [[ -d "${DEST_USER}" ]]; then
        rm -f "${DEST_USER}"/pf-*.container "${DEST_USER}"/pf-*.pod "${DEST_USER}"/pf-*.network "${DEST_USER}"/pf-*.volume "${DEST_USER}"/pf-*.target
        reload_systemd
        log_info "Removed pf quadlets from ${DEST_USER}"
    else
        log_warn "Quadlet destination does not exist: ${DEST_USER}"
    fi
}

list_quadlets() {
    if [[ -d "${DEST_USER}" ]]; then
        ls -1 "${DEST_USER}"/pf-* 2>/dev/null || echo "No pf quadlet files installed in ${DEST_USER}"
    else
        echo "No quadlet directory: ${DEST_USER}"
    fi
}

status_quadlets() {
    list_quadlets
    if command -v systemctl >/dev/null 2>&1; then
        echo ""
        ${SYSTEMCTL} list-unit-files | grep -E '^pf-.*\.(service|target)' || true
    else
        log_warn "systemctl not found; cannot query unit status"
    fi
}

usage() {
    cat <<EOF
Usage: $0 [--install|--remove|--list|--status]
EOF
}

case "${1:-}" in
    --install) install_quadlets ;;
    --remove) remove_quadlets ;;
    --list) list_quadlets ;;
    --status) status_quadlets ;;
    *) usage; exit 1 ;;
esac
