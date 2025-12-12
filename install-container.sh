#!/usr/bin/env bash
# Container-based installer for pf
# Builds pf in a container and copies the executable to the host.

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
IMAGE_NAME="pf-runner:local"
BASE_IMAGE="localhost/pf-base:latest"
RUNTIME=""
PREFIX="/usr/local"

# Color output helpers
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info() { echo -e "${BLUE}[pf-install]${NC} $*"; }
log_success() { echo -e "${GREEN}[pf-install]${NC} $*"; }
log_warn() { echo -e "${YELLOW}[pf-install]${NC} $*"; }
log_error() { echo -e "${RED}[pf-install]${NC} $*"; }

usage() {
  cat <<'USAGE'
Usage: ./install-container.sh [--image NAME] [--runtime docker|podman] [--prefix PATH]

Builds pf in a container and installs it to /usr/local/bin on the host.

Options:
  --image NAME       Image tag to build (default: pf-runner:local)
  --runtime NAME     Container runtime to use (auto-detects docker then podman)
  --prefix PATH      Install prefix (default: /usr/local). Binary goes to PREFIX/bin/pf
  -h, --help         Show this help
USAGE
}

choose_runtime() {
  if [[ -n "${RUNTIME}" ]]; then
    if ! command -v "${RUNTIME}" >/dev/null 2>&1; then
      log_error "Specified runtime '${RUNTIME}' not found"
      exit 1
    fi
    return
  fi
  if command -v docker >/dev/null 2>&1; then
    RUNTIME="docker"
  elif command -v podman >/dev/null 2>&1; then
    RUNTIME="podman"
  else
    log_error "No container runtime found (install docker or podman)"
    exit 1
  fi
}

build_base_image() {
  log_info "Building base image '${BASE_IMAGE}' with ${RUNTIME}..."
  ${RUNTIME} build -f "${ROOT_DIR}/containers/dockerfiles/Dockerfile.base" -t "${BASE_IMAGE}" "${ROOT_DIR}"
  log_success "Base image built: ${BASE_IMAGE}"
}

build_image() {
  log_info "Building image '${IMAGE_NAME}' with ${RUNTIME}..."
  ${RUNTIME} build -f "${ROOT_DIR}/containers/dockerfiles/Dockerfile.pf-runner" -t "${IMAGE_NAME}" "${ROOT_DIR}"
  log_success "Image built: ${IMAGE_NAME}"
}

copy_pf_to_host() {
  local install_path="${PREFIX}/bin"
  local install_dir="${PREFIX}/lib/pf-runner"

  log_info "Copying pf from container to ${install_path}/pf..."

  # Try to create directories first (will fail if no permission)
  if ! mkdir -p "${install_dir}" 2>/dev/null || ! mkdir -p "${install_path}" 2>/dev/null; then
    if [[ $EUID -ne 0 ]]; then
      log_error "Cannot create ${install_path} or ${install_dir}. Run with sudo or use --prefix ~/.local"
      exit 1
    fi
  fi

  # Check if we have write permission
  if [[ ! -w "${install_path}" ]] || [[ ! -w "${install_dir}" ]]; then
    if [[ $EUID -ne 0 ]]; then
      log_error "Cannot write to ${install_path}. Run with sudo or use --prefix ~/.local"
      exit 1
    fi
  fi

  # Create a temporary container to copy files from
  local container_id
  container_id=$(${RUNTIME} create "${IMAGE_NAME}" /bin/true)

  # Copy pf-runner directory from container
  ${RUNTIME} cp "${container_id}:/app/pf-runner/." "${install_dir}/"

  # Remove the temporary container
  ${RUNTIME} rm "${container_id}" >/dev/null

  # Make the main script executable
  chmod +x "${install_dir}/pf_parser.py"

  # Create the pf executable in bin directory
  cat > "${install_path}/pf" <<EOF
#!/usr/bin/env bash
set -euo pipefail
exec python3 "${install_dir}/pf_parser.py" "\$@"
EOF
  chmod +x "${install_path}/pf"

  log_success "pf installed to ${install_path}/pf"
}

# Parse args
while [[ $# -gt 0 ]]; do
  case "$1" in
    --image)
      IMAGE_NAME="$2"; shift 2;;
    --runtime)
      RUNTIME="$2"; shift 2;;
    --prefix)
      PREFIX="$2"; shift 2;;
    -h|--help)
      usage; exit 0;;
    *)
      echo "Unknown option: $1" >&2; usage; exit 1;;
  esac
done

log_info "pf container-based installer"
log_info "============================="

choose_runtime
build_base_image
build_image
copy_pf_to_host

log_success "Installation complete!"
log_info ""
log_info "Verify with: ${PREFIX}/bin/pf --version"
log_info "List tasks:  ${PREFIX}/bin/pf list"

# Check if install path is in PATH
if [[ ":${PATH}:" != *":${PREFIX}/bin:"* ]]; then
  log_warn ""
  log_warn "Note: ${PREFIX}/bin is not in your PATH."
  log_warn "Add it with: export PATH=\"${PREFIX}/bin:\$PATH\""
fi

exit 0
