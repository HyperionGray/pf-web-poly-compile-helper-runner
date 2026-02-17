#!/usr/bin/env bash
#
# JSON5 helpers for scripts in this repo.
# Intended to be sourced (not executed).
#

if [[ -n "${__PF_JSON5_LIB_SOURCED:-}" ]]; then
  return 0
fi
__PF_JSON5_LIB_SOURCED=1

pf_json5_get() {
  local config_path="${1:-}"
  local dotted_key="${2:-}"
  local default="${3:-}"

  if [[ -z "$config_path" || -z "$dotted_key" ]]; then
    printf '%s\n' "$default"
    return 0
  fi
  if [[ ! -f "$config_path" ]]; then
    printf '%s\n' "$default"
    return 0
  fi
  if ! command -v python3 >/dev/null 2>&1; then
    printf '%s\n' "$default"
    return 0
  fi

  python3 - "$config_path" "$dotted_key" "$default" <<'PY' 2>/dev/null || printf '%s\n' "$default"
import sys

cfg_path = sys.argv[1]
key = sys.argv[2]
default = sys.argv[3]

try:
    import json5  # type: ignore
except Exception:
    print(default)
    raise SystemExit(0)

try:
    with open(cfg_path, "r", encoding="utf-8") as f:
        data = json5.load(f)
except Exception:
    print(default)
    raise SystemExit(0)

cur = data
for part in key.split("."):
    if not isinstance(cur, dict) or part not in cur:
        print(default)
        raise SystemExit(0)
    cur = cur[part]

if isinstance(cur, bool):
    print("true" if cur else "false")
elif cur is None:
    print(default)
else:
    print(str(cur))
PY
}

