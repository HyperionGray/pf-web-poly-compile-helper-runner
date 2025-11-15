#!/bin/bash
cat > Makefile << EOL
SHELL := /bin/bash

# Central Python from the user's venv (per workspace conventions)
PF_PY := /home/punk/.venv/bin/python
PF_SCRIPT := pf_parser.py
PF_LINK := pf

.PHONY: default help clean shebang perms symlink setup test distclean install-local uninstall-local build install

default: setup

help:
	@echo "Targets:"
	@echo "  setup      - clean, enforce shebang, create 'pf' symlink"
	@echo "  test       - smoke test 'pf' against test.pf"
	@echo "  clean      - remove pyc/__pycache__ and editor backups"
	@echo "  distclean  - clean + remove 'pf' symlink"
	@echo "  install-local   - install a global 'pf' in ~/.local/bin"
	@echo "  uninstall-local - remove the global 'pf' from ~/.local/bin"
	@echo "  build      - create a static executable"
	@echo "  install    - install the static executable to /usr/local/bin"

# Always do cleanup before all else
setup: clean shebang perms symlink
	@echo "Setup complete. Try: ./$(PF_LINK) test.pf --list"

shebang:
	@# Ensure the CLI uses the central venv python in the shebang
	@if [ -f "$(PF_SCRIPT)" ]; then \\
	  first_line=$$(head -n 1 "$(PF_SCRIPT)"); \\
	  if [ "$$first_line" != "#!$(PF_PY)" ]; then \\
	    sed -i '1s|^.*$$|#!$(PF_PY)|' "$(PF_SCRIPT)"; \\
	    echo "Updated shebang to $(PF_PY)"; \\
	  fi; \\
	fi

perms:
	@# Ensure executable bit for the CLI script
	@if [ -f "$(PF_SCRIPT)" ]; then chmod +x "$(PF_SCRIPT)"; fi

symlink:
	@# Create/refresh a repo-local 'pf' symlink pointing to the CLI
	@ln -sfn ./$(PF_SCRIPT) $(PF_LINK)
	@ls -l $(PF_LINK)

test: setup
	@set -e; \\
	./$(PF_LINK) test.pf --list; \\
	./$(PF_LINK) test.pf hello

clean:
	@# Remove caches and editor backup files
	@find . -type d -name __pycache__ -prune -exec rm -rf {} + || true
	@find . -type f -name '*.pyc' -delete || true
	@find . -type f -name '*~' -delete || true
	@rm -rf build dist *.spec

distclean: clean
	@rm -f $(PF_LINK)
	@echo "Removed $(PF_LINK) symlink"

install-local: setup
	@install -d "$(HOME)/.local/bin"
	@# Install as a symlink so the wrapper can resolve back to the repo
	@ln -sfn "$(abspath pf_parser.py)" "/usr/local/bin/pf"
	@echo "Installed symlink: /usr/local/bin/pf -> $(abspath pf_parser.py)"

uninstall-local:
	@rm -f "/usr/local/bin/pf"
	@echo "Removed: /usr/local/bin/pf"

build:
	@echo "Building static executable..."
	@$(PF_PY) -m PyInstaller --onefile $(PF_SCRIPT)
	@echo "Build complete. Executable at dist/$(PF_SCRIPT:.py=)"

install: build
	@echo "Installing executable to /usr/local/bin/pf..."
	@sudo install dist/pf_parser /usr/local/bin/pf
	@echo "Installation complete."
EOL
