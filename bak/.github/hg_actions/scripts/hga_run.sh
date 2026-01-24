#!/usr/bin/env bash
set -euo pipefail

action_file="${1:-}"
execute="${2:-true}"

if [[ -z "${action_file}" ]]; then
  echo "Usage: pf -f hg_actions/Pfyfile.hgactions.pf run hga-run file=<action-file> [execute=true|false]" >&2
  exit 1
fi

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

action_file_path="${action_file}"
if [[ "${action_file_path}" != /* ]]; then
  action_file_path="${repo_root}/${action_file_path}"
fi

if [[ ! -f "${action_file_path}" ]]; then
  echo "Action file not found: ${action_file_path}" >&2
  exit 1
fi

python_bin=""
python_candidates=(
  "/home/punk/.venv/bin/python"
  "${repo_root}/venv/bin/python"
)

for candidate in "${python_candidates[@]}"; do
  if [[ -x "${candidate}" ]]; then
    python_bin="${candidate}"
    break
  fi
done

if [[ -z "${python_bin}" ]]; then
  if command -v python3 >/dev/null 2>&1; then
    python_bin="$(command -v python3)"
  elif command -v python >/dev/null 2>&1; then
    python_bin="$(command -v python)"
  fi
fi

if [[ -z "${python_bin}" || ! -x "${python_bin}" ]]; then
  echo "Python not found (tried /home/punk/.venv, ${repo_root}/venv, and PATH)" >&2
  exit 1
fi

cd "${repo_root}"

case "${execute}" in
  true)
    "${python_bin}" -m hg_actions.cli run "${action_file_path}" --execute
    ;;
  false)
    "${python_bin}" -m hg_actions.cli run "${action_file_path}" --dry-run
    ;;
  *)
    echo "Invalid execute value: ${execute} (expected true|false)" >&2
    exit 2
    ;;
esac
