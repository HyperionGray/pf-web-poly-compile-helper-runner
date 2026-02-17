#!/bin/bash
# Make build.sh executable
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
chmod +x "${REPO_ROOT}/scripts/build.sh"
echo "Made build.sh executable"
