#!/usr/bin/env bash
<<<<<<< HEAD
# Container-based installer for pf
# Builds the pf-runner image and installs the pf executable directly to /usr/local/bin.
=======
# Simple installer for pf
# Installs pf directly to /usr/local/bin (or user-specified path) with dependencies.
>>>>>>> main

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
<<<<<<< HEAD
IMAGE_NAME="pf-runner:local"
BASE_IMAGE="localhost/pf-base:latest"
RUNTIME=""

usage() {
  cat <<'USAGE'
Usage: ./install.sh [--image NAME] [--runtime docker|podman]

Builds the pf-runner container image (Dockerfile.pf-runner) and installs the pf
executable directly to /usr/local/bin using a privileged container with mounted volume.

Options:
  --image NAME       Image tag to build/use (default: pf-runner:local)
  --runtime NAME     Container runtime to use (auto-detects docker then podman)
  -h, --help         Show this help

Note: This installation requires sudo privileges to write to /usr/local/bin.
=======
INSTALL_PATH="/usr/local/bin"
INSTALL_DIR="/usr/local/lib/pf-runner"
SKIP_DEPS=0

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
Usage: ./install.sh [--prefix PATH] [--skip-deps]

Installs the pf task runner directly to your system.

Options:
  --prefix PATH      Install prefix (default: /usr/local)
                     Binary goes to PREFIX/bin/pf
                     Library goes to PREFIX/lib/pf-runner
  --skip-deps        Skip installing Python dependencies (fabric, lark)
  -h, --help         Show this help

Examples:
  ./install.sh                    # Install to /usr/local/bin (requires sudo)
  ./install.sh --prefix ~/.local  # Install to ~/.local/bin (no sudo needed)
  sudo ./install.sh               # Install system-wide with sudo
>>>>>>> main
USAGE
}

check_python() {
  if ! command -v python3 >/dev/null 2>&1; then
    log_error "python3 not found. Please install Python 3.10+ first."
    exit 1
  fi
  
  local py_version
  py_version=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
  log_info "Found Python ${py_version}"
}

install_deps() {
  if [[ ${SKIP_DEPS} -eq 1 ]]; then
    log_info "Skipping dependency installation (--skip-deps)"
    return
  fi

  log_info "Installing Python dependencies..."
  
  # Check if pip is available
  if ! python3 -m pip --version >/dev/null 2>&1; then
    log_error "pip is not available. Please install python3-pip first."
    exit 1
  fi

  # Install dependencies - use --break-system-packages if needed (Python 3.11+)
  local pip_args=("fabric>=3.2,<4" "lark>=1.1.0")
  
  if python3 -m pip install --help 2>&1 | grep -q "break-system-packages"; then
    python3 -m pip install --break-system-packages "${pip_args[@]}" || {
      log_warn "System pip install failed, trying user install..."
      python3 -m pip install --user "${pip_args[@]}"
    }
  else
    python3 -m pip install "${pip_args[@]}" || {
      log_warn "System pip install failed, trying user install..."
      python3 -m pip install --user "${pip_args[@]}"
    }
  fi
  
  log_success "Dependencies installed"
}

<<<<<<< HEAD
build_base_image() {
  echo "[pf-install] Building base image '${BASE_IMAGE}' with ${RUNTIME}..."
  ${RUNTIME} build -f "${ROOT_DIR}/containers/dockerfiles/Dockerfile.base" -t "${BASE_IMAGE}" "${ROOT_DIR}"
  echo "[pf-install] Base image built: ${BASE_IMAGE}"
}

install_executable() {
  echo "[pf-install] Installing pf executable to /usr/local/bin..."
  
  # Check if we can write to /usr/local/bin
  if [[ ! -w /usr/local/bin ]] && [[ $EUID -ne 0 ]]; then
    echo "[pf-install] Warning: /usr/local/bin is not writable. You may need sudo privileges."
    echo "[pf-install] Attempting installation with sudo..."
    SUDO_CMD="sudo"
  else
    SUDO_CMD=""
  fi
  
  # Create a temporary container to extract the executable
  echo "[pf-install] Extracting pf executable from container..."
  TEMP_CONTAINER=$(${RUNTIME} create "${IMAGE_NAME}")
  
  # Copy the main Python script from the container
  if ! ${RUNTIME} cp "${TEMP_CONTAINER}:/app/pf-runner/pf_parser.py" /tmp/pf_parser.py; then
    echo "Error: Failed to extract pf_parser.py from container" >&2
    ${RUNTIME} rm "${TEMP_CONTAINER}" >/dev/null 2>&1 || true
    exit 1
  fi
  
  # Clean up the temporary container
  ${RUNTIME} rm "${TEMP_CONTAINER}" >/dev/null 2>&1 || true
  
  # Create a proper executable script with shebang
  cat > /tmp/pf-executable << 'EOF'
#!/usr/bin/env python3
EOF
  
  # Append the Python script content (skip the first line if it's a comment)
  tail -n +2 /tmp/pf_parser.py >> /tmp/pf-executable
  
  # Install the executable
  if [[ -n "${SUDO_CMD}" ]]; then
    ${SUDO_CMD} cp /tmp/pf-executable /usr/local/bin/pf
    ${SUDO_CMD} chmod +x /usr/local/bin/pf
    ${SUDO_CMD} chown root:root /usr/local/bin/pf
  else
    cp /tmp/pf-executable /usr/local/bin/pf
    chmod +x /usr/local/bin/pf
  fi
  
  # Clean up temporary files
  rm -f /tmp/pf-executable /tmp/pf_parser.py
  
  echo "[pf-install] pf executable installed to /usr/local/bin/pf"
  
  # Check if required Python packages are available
  echo "[pf-install] Checking Python dependencies..."
  if ! python3 -c "import fabric" >/dev/null 2>&1; then
    echo "[pf-install] Warning: Python 'fabric' package not found."
    echo "[pf-install] Install with: pip3 install 'fabric>=3.2,<4'"
  fi
  
  if ! python3 -c "import lark" >/dev/null 2>&1; then
    echo "[pf-install] Warning: Python 'lark' package not found."
    echo "[pf-install] Install with: pip3 install lark"
=======
install_pf() {
  log_info "Installing pf to ${INSTALL_PATH}/pf..."
  
  # Try to create directories first (will fail if no permission)
  if ! mkdir -p "${INSTALL_DIR}" 2>/dev/null || ! mkdir -p "${INSTALL_PATH}" 2>/dev/null; then
    if [[ $EUID -ne 0 ]]; then
      log_error "Cannot create ${INSTALL_PATH} or ${INSTALL_DIR}. Run with sudo or use --prefix ~/.local"
      exit 1
    fi
  fi
  
  # Check if we have write permission
  if [[ ! -w "${INSTALL_PATH}" ]] || [[ ! -w "${INSTALL_DIR}" ]]; then
    if [[ $EUID -ne 0 ]]; then
      log_error "Cannot write to ${INSTALL_PATH}. Run with sudo or use --prefix ~/.local"
      exit 1
    fi
  fi
  
  # Copy pf-runner source files
  cp -r "${ROOT_DIR}/pf-runner/"* "${INSTALL_DIR}/"
  
  # Make the main script executable
  chmod +x "${INSTALL_DIR}/pf_parser.py"
  chmod +x "${INSTALL_DIR}/pf" 2>/dev/null || true
  
  # Create the pf executable in bin directory
  cat > "${INSTALL_PATH}/pf" <<EOF
#!/usr/bin/env bash
set -euo pipefail
exec python3 "${INSTALL_DIR}/pf_parser.py" "\$@"
EOF
  chmod +x "${INSTALL_PATH}/pf"
  
  log_success "pf installed to ${INSTALL_PATH}/pf"
}

verify_install() {
  if [[ -x "${INSTALL_PATH}/pf" ]]; then
    log_success "Installation complete!"
    log_info ""
    log_info "Verify with: ${INSTALL_PATH}/pf --version"
    log_info "List tasks:  ${INSTALL_PATH}/pf list"
    
    # Check if install path is in PATH
    if [[ ":${PATH}:" != *":${INSTALL_PATH}:"* ]]; then
      log_warn ""
      log_warn "Note: ${INSTALL_PATH} is not in your PATH."
      log_warn "Add it with: export PATH=\"${INSTALL_PATH}:\$PATH\""
    fi
  else
    log_error "Installation verification failed"
    exit 1
>>>>>>> main
  fi
}

# Parse args
while [[ $# -gt 0 ]]; do
  case "$1" in
<<<<<<< HEAD
    --image)
      IMAGE_NAME="$2"; shift 2;;
    --runtime)
      RUNTIME="$2"; shift 2;;
=======
    --prefix)
      INSTALL_PATH="$2/bin"
      INSTALL_DIR="$2/lib/pf-runner"
      shift 2;;
    --skip-deps)
      SKIP_DEPS=1; shift;;
>>>>>>> main
    -h|--help)
      usage; exit 0;;
    *)
      echo "Unknown option: $1" >&2; usage; exit 1;;
  esac
done

<<<<<<< HEAD
choose_runtime
build_base_image
build_image
install_executable

echo "[pf-install] Installation complete!"
echo "[pf-install] The 'pf' command is now available in /usr/local/bin"
echo "[pf-install] Run 'pf list' to verify the installation."
echo ""
echo "[pf-install] Note: Make sure you have the required Python dependencies:"
echo "[pf-install]   pip3 install 'fabric>=3.2,<4' lark"
=======
log_info "pf-web-poly-compile-helper-runner installer"
log_info "============================================"

check_python
install_deps
install_pf
verify_install
>>>>>>> main

exit 0
