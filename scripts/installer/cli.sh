#!/usr/bin/env bash
set -euo pipefail

if declare -F __pf_installer_cli_loaded >/dev/null 2>&1; then
  return 0
fi
__pf_installer_cli_loaded() { :; }

installer_show_help() {
  cat << EOF
pf-runner Installation Script

USAGE:
  ./install.sh [OPTIONS]

OPTIONS:
  --mode MODE       Install mode: package (default), container, or native
  --package         Alias for --mode package
  --container       Alias for --mode container
  --native          Alias for --mode native

  --runtime RUNTIME Container runtime (podman|docker). Implies container mode
  --image IMAGE     pf-runner image name:tag (default: ${RUNNER_IMAGE_DEFAULT})
  --skip-build      Skip container image build (assumes images exist)
  --build-only      Build container images only (skip wrapper install)
  --no-wrapper      Skip installing the pf wrapper (container mode)

  --prefix PATH     Install prefix
                   Default: ${DEFAULT_PREFIX_NATIVE} for root,
                            ${DEFAULT_PREFIX_USER} for user installs

  --skip-deps       Skip installing system dependencies (native mode)
  --check           Run preflight checks only (no install changes)
  --help, -h        Show this help message
EOF
}

installer_parse_args() {
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --mode)
        MODE="${2:-}"
        shift 2
        ;;
      --mode=*)
        MODE="${1#*=}"
        shift
        ;;
      --package)
        MODE="package"
        shift
        ;;
      --container)
        MODE="container"
        shift
        ;;
      --native|--host)
        MODE="native"
        shift
        ;;
      --prefix)
        PREFIX="$(pf_abs_path "${2:-}")"
        PREFIX_SET=true
        shift 2
        ;;
      --prefix=*)
        PREFIX="$(pf_abs_path "${1#*=}")"
        PREFIX_SET=true
        shift
        ;;
      --runtime)
        CONTAINER_RT="${2:-}"
        CONTAINER_RT_SET=true
        MODE="container"
        shift 2
        ;;
      --runtime=*)
        CONTAINER_RT="${1#*=}"
        CONTAINER_RT_SET=true
        MODE="container"
        shift
        ;;
      --image)
        CONTAINER_IMAGE="${2:-}"
        MODE="container"
        shift 2
        ;;
      --image=*)
        CONTAINER_IMAGE="${1#*=}"
        MODE="container"
        shift
        ;;
      --skip-deps)
        SKIP_DEPS=true
        shift
        ;;
      --check)
        CHECK_ONLY=true
        shift
        ;;
      --skip-build)
        SKIP_BUILD=true
        MODE="container"
        shift
        ;;
      --build-only)
        BUILD_ONLY=true
        NO_WRAPPER=true
        MODE="container"
        shift
        ;;
      --no-wrapper)
        NO_WRAPPER=true
        MODE="container"
        shift
        ;;
      --help|-h)
        SHOW_HELP=true
        shift
        ;;
      *)
        log_error "Unknown option: $1"
        SHOW_HELP=true
        shift
        ;;
    esac
  done
}
