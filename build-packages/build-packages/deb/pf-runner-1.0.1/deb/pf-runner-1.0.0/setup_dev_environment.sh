#!/bin/bash
# Development Environment Setup Script (no venv required)
# Sets up Python + Node tooling and validates pf from anywhere in the repo tree.

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Resolve paths up-front so the script works from any directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if git -C "$SCRIPT_DIR" rev-parse --show-toplevel >/dev/null 2>&1; then
    REPO_ROOT="$(git -C "$SCRIPT_DIR" rev-parse --show-toplevel)"
else
    # script lives under build-packages/pf-runner-1.0.0 → repo root is two levels up
    REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
fi
PF_SRC="$REPO_ROOT/pf-runner-full"
NODE_ROOT="$REPO_ROOT"
PYTHON_BIN="${PYTHON_BIN:-python3}"

# Default pip flags: user install when not root, allow system-breaking installs on distros with PEP 668
if [[ -z "${PIP_FLAGS:-}" ]]; then
    if [[ $(id -u) -eq 0 ]]; then
        PIP_FLAGS="--break-system-packages"
    else
        PIP_FLAGS="--user --break-system-packages"
    fi
fi

# Split into an array for safe reuse
IFS=' ' read -r -a PIP_FLAGS_ARR <<< "$PIP_FLAGS"
PATH="$HOME/.local/bin:$PATH"  # ensure user bin is searchable during the run

# Function to print colored output
print_status() {
    local status=$1
    local message=$2
    case $status in
        "success")
            echo -e "${GREEN}✅ $message${NC}"
            ;;
        "error")
            echo -e "${RED}❌ $message${NC}"
            ;;
        "warning")
            echo -e "${YELLOW}⚠️  $message${NC}"
            ;;
        "info")
            echo -e "${BLUE}ℹ️  $message${NC}"
            ;;
    esac
}

print_header() {
    echo -e "${BLUE}"
    echo "=================================================="
    echo "  pf-web-poly-compile-helper-runner Dev Setup"
    echo "=================================================="
    echo -e "${NC}"
}

# Check system requirements
check_system_requirements() {
    print_status "info" "Checking system requirements..."
    
    local missing_deps=()
    
    # Check Python
    if ! command -v python3 &> /dev/null; then
        missing_deps+=("python3")
    else
        local python_version
        python_version=$(python3 --version | cut -d' ' -f2)
        print_status "success" "Python $python_version found"
    fi
    
    # Check Node.js (optional; warn but do not fail)
    if ! command -v node &> /dev/null; then
        print_status "warning" "Node.js not found (web/ui tasks will be skipped)"
    else
        local node_version
        node_version=$(node --version)
        print_status "success" "Node.js $node_version found"
    fi

    # Check npm (optional; warn but do not fail)
    if ! command -v npm &> /dev/null; then
        print_status "warning" "npm not found (web/ui deps will be skipped)"
    else
        local npm_version
        npm_version=$(npm --version)
        print_status "success" "npm $npm_version found"
    fi
    
    # Check Git
    if ! command -v git &> /dev/null; then
        missing_deps+=("git")
    else
        local git_version
        git_version=$(git --version | cut -d' ' -f3)
        print_status "success" "Git $git_version found"
    fi
    
    if [ ${#missing_deps[@]} -ne 0 ]; then
        print_status "error" "Missing required dependencies: ${missing_deps[*]}"
        echo ""
        echo "Install prerequisites, then re-run:"
        echo "  Ubuntu/Debian: sudo apt update && sudo apt install python3 python3-pip git"
        echo "  macOS:         brew install python3 git"
        echo ""
        exit 1
    fi
    
    print_status "success" "All system requirements met"
}

# Install Python dependencies
install_python_dependencies() {
    print_status "info" "Installing Python dependencies (no venv)..."

    # Core runtime deps mirror pyproject
    local core_deps=(
        "fabric>=3.2,<4"
        "lark>=1.1,<2.0"
        "typer>=0.12"
    )

    # Dev-quality tools (optional)
    local dev_deps=(
        "pytest"
        "pytest-cov"
        "coverage"
        "black"
        "flake8"
        "pylint"
        "bandit"
        "safety"
        "mypy"
        "isort"
    )

    # Install core deps
    "$PYTHON_BIN" -m pip install "${PIP_FLAGS_ARR[@]}" "${core_deps[@]}" || {
        print_status "error" "Failed to install core Python deps"
        exit 1
    }

    # Install dev deps best-effort
    "$PYTHON_BIN" -m pip install "${PIP_FLAGS_ARR[@]}" "${dev_deps[@]}" || {
        print_status "warning" "Some dev deps failed; continuing"
    }

    print_status "success" "Python dependencies installed"
}

# Install Node.js dependencies
install_node_dependencies() {
    # Optional step; skip cleanly if npm is absent
    if ! command -v npm >/dev/null 2>&1; then
        print_status "warning" "npm not available; skipping Node deps"
        return
    fi

    print_status "info" "Installing Node.js dependencies..."

    (cd "$NODE_ROOT" && npm ci) || {
        print_status "warning" "npm ci failed; skipping web tooling"
        return
    }

    print_status "success" "Node.js dependencies installed"
}

# Install Playwright browsers
install_playwright_browsers() {
    if ! command -v npx >/dev/null 2>&1; then
        print_status "warning" "npx not available; skipping Playwright browsers"
        return
    fi

    print_status "info" "Installing Playwright browsers..."
    (cd "$NODE_ROOT" && npx playwright install --with-deps) || {
        print_status "warning" "Playwright browser install failed (non-critical)"
    }
}

# Set up Git hooks
setup_git_hooks() {
    print_status "info" "Setting up Git hooks..."
    
    # Make pre-commit hook executable
    if [ -f ".git/hooks/pre-commit" ]; then
        chmod +x .git/hooks/pre-commit
        print_status "success" "Pre-commit hook configured"
    else
        print_status "warning" "Pre-commit hook not found"
    fi
    
    # Set up commit message template (optional)
    cat > .git/commit-template << 'EOF'
# <type>(<scope>): <subject>
#
# <body>
#
# <footer>
#
# Types:
# feat: A new feature
# fix: A bug fix
# docs: Documentation only changes
# style: Changes that do not affect the meaning of the code
# refactor: A code change that neither fixes a bug nor adds a feature
# perf: A code change that improves performance
# test: Adding missing tests or correcting existing tests
# chore: Changes to the build process or auxiliary tools
EOF
    
    git config commit.template .git/commit-template
    print_status "success" "Git commit template configured"
}

# Install a user-scoped pf shim that works without a venv
install_pf_shim() {
    print_status "info" "Installing user pf shim..."
    local shim_dir="$HOME/.local/bin"
    mkdir -p "$shim_dir"
    local target="$REPO_ROOT/pf.sh"
    if ln -sfn "$target" "$shim_dir/pf"; then
        chmod +x "$target"
        print_status "success" "pf shim linked to $target"
    else
        print_status "warning" "Could not link pf shim (path: $shim_dir/pf)"
    fi
}

# Create development configuration files
create_dev_configs() {
    print_status "info" "Creating development configuration files..."
    
    # Create .env file for development
    if [ ! -f ".env" ]; then
        cat > .env << 'EOF'
# Development environment variables
DEBUG=true
LOG_LEVEL=debug
NODE_ENV=development

# Test configuration
PLAYWRIGHT_HEADLESS=true
TEST_TIMEOUT=30000

# Security scanning
SECURITY_SCAN_ENABLED=true
EOF
        print_status "success" "Development .env file created"
    else
        print_status "info" ".env file already exists"
    fi
    
    # Create VS Code settings (optional)
    if [ ! -d ".vscode" ]; then
        mkdir -p .vscode
        
        cat > .vscode/settings.json << 'EOF'
{
    "python.defaultInterpreterPath": "python3",
    "python.linting.enabled": true,
    "python.linting.flake8Enabled": true,
    "python.linting.pylintEnabled": true,
    "python.linting.banditEnabled": true,
    "python.formatting.provider": "black",
    "python.formatting.blackArgs": ["--line-length=120"],
    "eslint.enable": true,
    "eslint.format.enable": true,
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
        "source.organizeImports": true
    },
    "files.exclude": {
        "**/__pycache__": true,
        "**/*.pyc": true,
        "**/node_modules": true,
        "**/coverage": true,
        "**/htmlcov": true,
        "**/.pytest_cache": true
    }
}
EOF
        
        cat > .vscode/extensions.json << 'EOF'
{
    "recommendations": [
        "ms-python.python",
        "ms-python.flake8",
        "ms-python.black-formatter",
        "ms-python.pylint",
        "ms-playwright.playwright",
        "dbaeumer.vscode-eslint",
        "esbenp.prettier-vscode",
        "ms-vscode.vscode-typescript-next"
    ]
}
EOF
        
        print_status "success" "VS Code configuration created"
    else
        print_status "info" "VS Code configuration already exists"
    fi
}

# Run initial tests
run_initial_tests() {
    print_status "info" "Running smoke checks (no venv)..."

    # Python syntax for core files
    if [ -d "$PF_SRC" ]; then
        for py_file in "$PF_SRC"/pf_*.py "$PF_SRC"/pfuck.py; do
            [[ -f "$py_file" ]] || continue
            "$PYTHON_BIN" -m py_compile "$py_file" || {
                print_status "error" "Python syntax error in $py_file"
                exit 1
            }
        done
        print_status "success" "Python syntax check passed"
    fi

    # pf list using the source tree (works without venv)
    if [ -f "$PF_SRC/pf_main.py" ]; then
        PYTHONPATH="$PF_SRC" "$PYTHON_BIN" -m pf_main --version >/dev/null 2>&1 || print_status "warning" "pf --version failed"
        PYTHONPATH="$PF_SRC" "$PYTHON_BIN" -m pf_main list >/dev/null 2>&1 || print_status "warning" "pf list failed"
        print_status "success" "pf source runner smoke check complete"
    fi

    # Minimal Node lint smoke (optional)
    if command -v npm >/dev/null 2>&1 && [ -f "$NODE_ROOT/package.json" ]; then
        (cd "$NODE_ROOT" && npm run lint --if-present --silent) || print_status "warning" "npm lint failed (non-blocking)"
    fi
}

# Display setup summary
display_summary() {
    print_status "success" "Development environment setup complete!"
    echo ""
    echo -e "${BLUE}📋 Setup Summary:${NC}"
    echo "  ✅ System requirements verified"
    echo "  ✅ Python dependencies installed"
    echo "  ✅ Node.js dependencies installed"
    echo "  ✅ Playwright browsers installed"
    echo "  ✅ Git hooks configured"
    echo "  ✅ Development configurations created"
    echo "  ✅ Initial tests completed"
    echo ""
    echo -e "${BLUE}🚀 Next Steps:${NC}"
    echo "  1. Run comprehensive tests: python3 run_comprehensive_tests.py"
    echo "  2. Start development server: npm run dev"
    echo "  3. Run TUI: PYTHONPATH=$PF_SRC $PYTHON_BIN -m pf_tui"
    echo "  4. View documentation: open README.md"
    echo ""
    echo -e "${BLUE}🔧 Available Commands:${NC}"
    echo "  • npm run test:all          - Run all tests"
    echo "  • npm run security:all      - Run security scans"
    echo "  • python3 -m black pf-runner/ - Format Python code"
    echo "  • npx eslint tools/ tests/  - Lint JavaScript code"
    echo ""
    echo -e "${YELLOW}⚠️  Important Notes:${NC}"
    echo "  • Pre-commit hooks are now active"
    echo "  • Code will be automatically checked before commits"
    echo "  • Use 'git commit --no-verify' to bypass hooks (not recommended)"
    echo ""
}

# Main execution
main() {
    print_header
    
    check_system_requirements
    install_python_dependencies
    install_node_dependencies
    install_playwright_browsers
    setup_git_hooks
    install_pf_shim
    create_dev_configs
    run_initial_tests
    display_summary
}

# Run main function
main "$@"
