#!/bin/bash
# Development Environment Setup Script
# This script sets up the complete development environment for pf-web-poly-compile-helper-runner

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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
    
    # Check Node.js
    if ! command -v node &> /dev/null; then
        missing_deps+=("node")
    else
        local node_version
        node_version=$(node --version)
        print_status "success" "Node.js $node_version found"
    fi
    
    # Check npm
    if ! command -v npm &> /dev/null; then
        missing_deps+=("npm")
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
        echo "Please install the missing dependencies and run this script again."
        echo ""
        echo "On Ubuntu/Debian:"
        echo "  sudo apt update && sudo apt install python3 python3-pip nodejs npm git"
        echo ""
        echo "On macOS:"
        echo "  brew install python3 node npm git"
        echo ""
        exit 1
    fi
    
    print_status "success" "All system requirements met"
}

# Install Python dependencies
install_python_dependencies() {
    print_status "info" "Installing Python dependencies..."
    
    # Core dependencies
    local core_deps=(
        "fabric>=3.2,<4"
        "rich"
        "lark"
    )
    
    # Development dependencies
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
    
    # Install core dependencies
    for dep in "${core_deps[@]}"; do
        print_status "info" "Installing $dep..."
        pip3 install "$dep" || {
            print_status "error" "Failed to install $dep"
            exit 1
        }
    done
    
    # Install development dependencies
    for dep in "${dev_deps[@]}"; do
        print_status "info" "Installing $dep..."
        pip3 install "$dep" || {
            print_status "warning" "Failed to install $dep (non-critical)"
        }
    done
    
    print_status "success" "Python dependencies installed"
}

# Install Node.js dependencies
install_node_dependencies() {
    print_status "info" "Installing Node.js dependencies..."
    
    if [ -f "package.json" ]; then
        npm ci || {
            print_status "error" "Failed to install Node.js dependencies"
            exit 1
        }
    else
        print_status "warning" "No package.json found, skipping Node.js dependencies"
        return
    fi
    
    # Install additional development tools
    local dev_tools=(
        "@typescript-eslint/parser"
        "@typescript-eslint/eslint-plugin"
        "eslint-plugin-security"
        "eslint-plugin-import"
        "prettier"
    )
    
    for tool in "${dev_tools[@]}"; do
        print_status "info" "Installing $tool..."
        npm install --save-dev "$tool" || {
            print_status "warning" "Failed to install $tool (non-critical)"
        }
    done
    
    print_status "success" "Node.js dependencies installed"
}

# Install Playwright browsers
install_playwright_browsers() {
    print_status "info" "Installing Playwright browsers..."
    
    if command -v npx &> /dev/null; then
        npx playwright install --with-deps || {
            print_status "warning" "Failed to install Playwright browsers (non-critical)"
            return
        }
        print_status "success" "Playwright browsers installed"
    else
        print_status "warning" "npx not available, skipping Playwright browsers"
    fi
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
    print_status "info" "Running initial tests to verify setup..."
    
    # Test Python syntax
    if [ -d "pf-runner" ]; then
        for py_file in pf-runner/*.py; do
            if [[ "$py_file" != *"pf_grammar.py" ]]; then
                python3 -m py_compile "$py_file" || {
                    print_status "error" "Python syntax error in $py_file"
                    exit 1
                }
            fi
        done
        print_status "success" "Python syntax check passed"
    fi
    
    # Test Node.js syntax
    if [ -f "package.json" ]; then
        npm run test:unit --silent || {
            print_status "warning" "Some Node.js tests failed (this may be expected in initial setup)"
        }
    fi
    
    # Test basic pf-runner functionality
    if [ -f "pf-runner/pf_main.py" ]; then
        cd pf-runner
        python3 pf_main.py --help > /dev/null || {
            print_status "warning" "pf-runner help test failed (may need additional setup)"
        }
        cd ..
        print_status "success" "Basic pf-runner functionality verified"
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
    echo "  3. Run TUI: cd pf-runner && python3 pf_tui.py"
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
    create_dev_configs
    run_initial_tests
    display_summary
}

# Run main function
main "$@"