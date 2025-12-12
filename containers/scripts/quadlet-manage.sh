#!/usr/bin/env bash
# quadlet-manage.sh — restart/disable helpers for pf-* quadlet units
set -euo pipefail

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; BLUE='\033[0;34m'; NC='\033[0m'
info(){ echo -e "${BLUE}[INFO]${NC} $*"; }
ok(){ echo -e "${GREEN}[OK]${NC} $*"; }
warn(){ echo -e "${YELLOW}[WARN]${NC} $*"; }
err(){ echo -e "${RED}[ERR]${NC} $*"; }

USER_MODE=true
if [[ ${EUID:-0} -eq 0 ]]; then USER_MODE=false; fi
SYSTEMCTL="systemctl --user"
$USER_MODE || SYSTEMCTL=systemctl

list_units(){
  $SYSTEMCTL list-unit-files | awk '/^pf-.*\.(service|target)/ {print $1}'
}

restart_all(){
  $SYSTEMCTL daemon-reload || warn "daemon-reload failed"
  mapfile -t units < <(list_units | grep '\.service$' || true)
  if [[ ${#units[@]} -eq 0 ]]; then
    warn "no pf-*.service units found"
    return 0
  fi
  info "restarting ${#units[@]} units"
  for u in "${units[@]}"; do
    info "restart: $u"
    $SYSTEMCTL restart "$u" || warn "failed: $u"
  done
  ok "restart-all complete"
}

disable_all(){
  $SYSTEMCTL daemon-reload || true
  mapfile -t units < <(list_units || true)
  local target="pf-suite.target"
  if printf '%s\n' "${units[@]}" | grep -q "^${target}$"; then
    info "disable: ${target}"
    $SYSTEMCTL disable --now "${target}" || true
  fi
  mapfile -t services < <(printf '%s\n' "${units[@]}" | grep '\.service$' || true)
  for u in "${services[@]}"; do
    info "stop+disable: $u"
    $SYSTEMCTL stop "$u" 2>/dev/null || true
    $SYSTEMCTL disable "$u" 2>/dev/null || true
  done
  ok "disable-all complete"
}

stop_all(){
  $SYSTEMCTL daemon-reload || true
  mapfile -t units < <(list_units | grep '\.service$' || true)
  if [[ ${#units[@]} -eq 0 ]]; then
    warn "no pf-*.service units found"
    return 0
  fi
  info "stopping ${#units[@]} units"
  for u in "${units[@]}"; do
    info "stop: $u"
    $SYSTEMCTL stop "$u" 2>/dev/null || true
  done
  ok "stop-all complete"
}

status_all(){
  $SYSTEMCTL daemon-reload || true
  list_units | while read -r u; do
    $SYSTEMCTL is-active "$u" >/dev/null 2>&1 && st=active || st=inactive
    $SYSTEMCTL is-enabled "$u" >/dev/null 2>&1 && en=enabled || en=disabled
    printf "%-28s %-10s %-10s\n" "$u" "$st" "$en"
  done || true
}

usage(){
  cat <<EOF
Usage: $0 <restart-all|disable-all|stop-all|status-all|list>
EOF
}

case "${1:-}" in
  restart-all) restart_all ;;
  disable-all) disable_all ;;
  stop-all)    stop_all ;;
  status-all)  status_all ;;
  list)        list_units ;;
  *) usage; exit 1 ;;
 esac
