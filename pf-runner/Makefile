SHELL := /bin/bash

# Central Python from the user's venv (per workspace conventions)
PF_PY := /home/punk/.venv/bin/python
PF_SCRIPT := pf_parser.py
PF_LINK := pf

.PHONY: default help clean shebang perms symlink setup test distclean install-local uninstall-local build install install-completions uninstall-completions

default: setup

help:
	@echo "Targets:"
	@echo "  setup      - clean, enforce shebang, create 'pf' symlink"
	@echo "  test       - smoke test 'pf' against test.pf"
	@echo "  clean      - remove pyc/__pycache__ and editor backups"
	@echo "  distclean  - clean + remove 'pf' symlink"
	@echo "  install-local        - install a global 'pf' in ~/.local/bin"
	@echo "  uninstall-local      - remove the global 'pf' from ~/.local/bin"
	@echo "  install-completions  - install shell completions (bash and zsh)"
	@echo "  uninstall-completions - remove shell completions"
	@echo "  build      - create a static executable"
	@echo "  install    - install the static executable to /usr/local/bin (includes completions)"

# Always do cleanup before all else
setup: clean shebang perms symlink
	@echo "Setup complete. Try: ./$(PF_LINK) test.pf --list"

shebang:
	@# Ensure the CLI uses the central venv python in the shebang
	@if [ -f "$(PF_SCRIPT)" ]; then \
	  first_line=$$(head -n 1 "$(PF_SCRIPT)"); \
	  if [ "$$first_line" != "#!$(PF_PY)" ]; then \
	    sed -i '1s|^.*$$|#!$(PF_PY)|' "$(PF_SCRIPT)"; \
	    echo "Updated shebang to $(PF_PY)"; \
	  fi; \
	fi

perms:
	@# Ensure executable bit for the CLI script
	@if [ -f "$(PF_SCRIPT)" ]; then chmod +x "$(PF_SCRIPT)"; fi

symlink:
	@# Create/refresh a repo-local 'pf' symlink pointing to the CLI
	@ln -sfn ./$(PF_SCRIPT) $(PF_LINK)
	@ls -l $(PF_LINK)

test: setup
	@set -e; \
	./$(PF_LINK) test.pf --list; \
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
	@ln -sfn "$(abspath pf_parser.py)" "$(HOME)/.local/bin/pf"
	@echo "Installed symlink: $(HOME)/.local/bin/pf -> $(abspath pf_parser.py)"
	@echo ""
	@echo "To install shell completions, run: make install-completions"

uninstall-local:
	@rm -f "$(HOME)/.local/bin/pf"
	@echo "Removed: $(HOME)/.local/bin/pf"

install-completions:
	@echo "Installing shell completions..."
	@# Install bash completion
	@if [ -d /etc/bash_completion.d ]; then \
		sudo install -m 644 completions/pf-completion.bash /etc/bash_completion.d/pf; \
		echo "Installed bash completion to /etc/bash_completion.d/pf"; \
	elif [ -d "$(HOME)/.local/share/bash-completion/completions" ]; then \
		install -d "$(HOME)/.local/share/bash-completion/completions"; \
		install -m 644 completions/pf-completion.bash "$(HOME)/.local/share/bash-completion/completions/pf"; \
		echo "Installed bash completion to $(HOME)/.local/share/bash-completion/completions/pf"; \
	else \
		echo "Warning: Could not find bash completion directory"; \
	fi
	@# Install zsh completion
	@if [ -d /usr/local/share/zsh/site-functions ]; then \
		sudo install -m 644 completions/_pf /usr/local/share/zsh/site-functions/_pf; \
		echo "Installed zsh completion to /usr/local/share/zsh/site-functions/_pf"; \
	elif [ -d "$(HOME)/.zsh/completions" ]; then \
		install -d "$(HOME)/.zsh/completions"; \
		install -m 644 completions/_pf "$(HOME)/.zsh/completions/_pf"; \
		echo "Installed zsh completion to $(HOME)/.zsh/completions/_pf"; \
		echo "Add 'fpath=(~/.zsh/completions \$$fpath)' to your ~/.zshrc if not already present"; \
	else \
		echo "Warning: Could not find zsh completion directory"; \
	fi
	@echo ""
	@echo "Restart your shell or source the completion files to enable completions"

uninstall-completions:
	@echo "Removing shell completions..."
	@rm -f /etc/bash_completion.d/pf "$(HOME)/.local/share/bash-completion/completions/pf"
	@rm -f /usr/local/share/zsh/site-functions/_pf "$(HOME)/.zsh/completions/_pf"
	@echo "Removed completion files"

build: clean
	@echo "Cleaning virtual environment..."
	@pf venv-clean
	@echo "Building static executable..."
	@$(PF_PY) -m PyInstaller --onefile $(PF_SCRIPT)
	@echo "Build complete. Executable at dist/$(PF_SCRIPT:.py=)"

install: build install-completions
	@echo "Installing executable to /usr/local/bin/pf..."
	@sudo install dist/pf_parser /usr/local/bin/pf
	@echo "Installation complete."
