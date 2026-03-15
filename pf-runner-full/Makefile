SHELL := /bin/bash

REPO_VENV := $(abspath .)/.venv/bin/python
PF_PY := $(shell if [ -x "$(REPO_VENV)" ]; then echo "$(REPO_VENV)"; elif command -v python3 >/dev/null 2>&1; then command -v python3; else command -v python; fi)
PIP := $(PF_PY) -m pip

# Prefer the system interpreter for global installs so we don't depend on the repo venv.
SYSTEM_PY := $(shell if [ -x /usr/bin/python3 ]; then echo /usr/bin/python3; elif command -v python3 >/dev/null 2>&1; then command -v python3; else command -v python; fi)
SYSTEM_PIP := $(SYSTEM_PY) -m pip

PREFIX ?= /usr/local
DESTDIR ?=
BINDIR ?= $(DESTDIR)$(PREFIX)/bin
BASH_COMPLETIONS_DIR ?= /usr/share/bash-completion/completions
ZSH_COMPLETIONS_DIR ?= /usr/share/zsh/site-functions
CODENAME ?= bookworm
PUBLISH_CMD ?= echo "Set PUBLISH_CMD to upload (e.g., aws s3 sync apt-repo s3://your-bucket/apt-repo/)"
DEB_FILE ?= $(firstword $(wildcard ../build-packages/deb/pf-runner_*.deb ../debian/build/pf-runner_*.deb))
DEB_PKG ?= pf-runner

PF_LINK := pf
PF_CLI := pf_universal
TEST_PF ?= ../tests/fixtures/installer_test.pf

# Allow callers to control pip flags (PEP 668 on Debian/Ubuntu requires --break-system-packages for system installs).
PIP_FLAGS ?= --break-system-packages
# Avoid attempting to uninstall distro packages during system install.
PIP_INSTALL_FLAGS ?= --ignore-installed
# Avoid touching distro-managed pip/setuptools/wheel unless explicitly requested.
SKIP_PIP_UPGRADE ?= 1

.PHONY: help local-install local_install link setup-venv test clean distclean install install-deb install-pip install-user install-completions uninstall build-static

help:
	@echo "Targets:"
	@echo "  local-install      - create repo-local './pf' shim (native runner)"
	@echo "  setup-venv         - create .venv and install deps (editable)"
	@echo "  build-static       - build static executable using PyInstaller"
	@echo "  install / install-deb - install packaged .deb via dpkg -i (uses sudo if needed)"
	@echo "  apt-repo           - build .deb (if needed) and regenerate apt repo under ../build-packages/deb/apt-repo (CODENAME=$(CODENAME))"
	@echo "  install-pip        - fallback pip install (not preferred)"
	@echo "  install-user   - user install via pip --user"
	@echo "  install-completions - install bash/zsh completions"
	@echo "  test           - smoke test pf against $(TEST_PF)"
	@echo "  clean          - remove __pycache__ and *.pyc"
	@echo "  distclean      - clean and remove the local shim"
	@echo "  publish-apt    - regen apt repo (uses apt-repo target) then run PUBLISH_CMD to upload"

setup-venv:
	@set -e; \
		if [ ! -x "$(REPO_VENV)" ]; then python3 -m venv --without-pip .venv; fi; \
		if ! "$(PF_PY)" -m pip --version >/dev/null 2>&1; then \
		  echo "Rebuilding .venv (pip missing/broken)"; \
		  rm -rf .venv; \
		  python3 -m venv --without-pip .venv; \
		fi; \
		"$(PF_PY)" -m ensurepip --upgrade --default-pip >/dev/null; \
		$(PIP) install -U pip setuptools wheel >/dev/null; \
		$(PIP) install -e .

link:
	@chmod +x "$(PF_CLI)"
	@ln -sfn ./$(PF_CLI) $(PF_LINK)
	@ls -l $(PF_LINK)

local-install: setup-venv link

local_install: local-install

test: local-install
	@$(PF_PY) -m pf_main -f "$(TEST_PF)" list

install: install-deb

install-deb:
	@set -e; \
	if [ -z "$(DEB_FILE)" ]; then \
	  echo "No .deb found. Set DEB_FILE=path/to/pf-runner_<ver>.deb"; \
	  exit 1; \
	fi; \
	SUDO_CMD=""; \
	if [ "$$EUID" -ne 0 ] && [ -z "$(NO_SUDO)" ]; then SUDO_CMD="sudo"; fi; \
	echo "Installing $(DEB_FILE) with $${SUDO_CMD:+$${SUDO_CMD} }dpkg -i"; \
	$$SUDO_CMD dpkg -i "$(DEB_FILE)"; \
	echo "pf installed from $(DEB_FILE)"

.PHONY: apt-repo
apt-repo:
	@set -e; \
	DEB_LATEST="../build-packages/deb/pf-runner_latest.deb"; \
	if [ ! -f $$DEB_LATEST ]; then \
	  echo "pf-runner_latest.deb not found; building .deb first..."; \
	  (cd ../build-packages/deb/pf-runner-1.0.0/debian && ./build-deb.sh 1.0.1); \
	  ln -sf pf-runner_1.0.1.deb ../build-packages/deb/pf-runner_latest.deb; \
	fi; \
	echo "Generating apt repo for CODENAME=$(CODENAME)..."; \
	(cd ../build-packages/deb && CODENAME=$(CODENAME) DEB_PATH=pf-runner_latest.deb ./make-apt-repo.sh); \
	echo "Apt repo ready at ../build-packages/deb/apt-repo (unsigned)."

.PHONY: publish-apt
publish-apt: apt-repo
	@cd ../build-packages/deb && $(PUBLISH_CMD) apt-repo

install-pip:
	@set -e; \
	SUDO_CMD=""; \
	if [ "$(PREFIX)" = "/usr/local" ] && [ "$$EUID" -ne 0 ] && [ -z "$(NO_SUDO)" ]; then SUDO_CMD="sudo"; fi; \
	echo "Using $${SUDO_CMD:+$${SUDO_CMD} }$(SYSTEM_PY) for install"; \
	$(SYSTEM_PY) -m ensurepip --upgrade >/dev/null 2>&1 || true; \
	if [ "$(SKIP_PIP_UPGRADE)" != "1" ]; then \
	  $$SUDO_CMD $(SYSTEM_PIP) install -U $(PIP_FLAGS) pip setuptools wheel >/dev/null; \
	fi; \
	$$SUDO_CMD $(SYSTEM_PIP) install $(PIP_FLAGS) $(PIP_INSTALL_FLAGS) --prefix "$(PREFIX)" .; \
	echo "pf installed to $(PREFIX)/bin (add to PATH if needed)"

install-user:
	@set -e; \
	$(SYSTEM_PY) -m ensurepip --upgrade >/dev/null 2>&1 || true; \
	$(SYSTEM_PIP) install -U pip setuptools wheel >/dev/null; \
	$(SYSTEM_PIP) install --user .; \
	echo "pf installed to user site-packages (usually $$HOME/.local/bin)"

install-completions:
	@set -e; \
	SUDO_CMD=""; \
	if echo "$(BASH_COMPLETIONS_DIR) $(ZSH_COMPLETIONS_DIR) $(PREFIX)" | grep -q "^/usr" && [ "$$EUID" -ne 0 ] && [ -z "$(NO_SUDO)" ]; then SUDO_CMD="sudo"; fi; \
	BASH_DIR="$(DESTDIR)$(BASH_COMPLETIONS_DIR)"; \
	ZSH_DIR="$(DESTDIR)$(ZSH_COMPLETIONS_DIR)"; \
	$$SUDO_CMD install -d "$${BASH_DIR}" "$${ZSH_DIR}"; \
	$$SUDO_CMD install -m 0644 completions/pf-completion.bash "$${BASH_DIR}/pf"; \
	$$SUDO_CMD install -m 0644 completions/_pf "$${ZSH_DIR}/_pf"; \
	echo "Completions installed to $${BASH_DIR} (bash) and $${ZSH_DIR} (zsh)"

uninstall:
	@set -e; \
	SUDO_CMD=""; \
	if [ "$(PREFIX)" = "/usr/local" ] && [ "$$EUID" -ne 0 ] && [ -z "$(NO_SUDO)" ]; then SUDO_CMD="sudo"; fi; \
	$$SUDO_CMD dpkg -r $(DEB_PKG) 2>/dev/null || true; \
	$$SUDO_CMD $(SYSTEM_PIP) uninstall -y pf-runner 2>/dev/null || true

clean:
	@find . -type d -name __pycache__ -prune -exec rm -rf {} + || true
	@find . -type f -name '*.pyc' -delete || true
	@rm -rf build dist *.spec

distclean: clean
	@rm -f $(PF_LINK)
	@echo "Removed local pf shim"

build-static: setup-venv
	@echo "Building static executable with PyInstaller..."
	@$(PIP) install pyinstaller >/dev/null 2>&1
	@$(REPO_VENV) -m PyInstaller --onefile --name pf-static pf_main.py
	@if [ -f dist/pf-static ]; then \
		mv dist/pf-static .; \
		echo "Static executable created: ./pf-static"; \
	else \
		echo "Error: Failed to create static executable"; \
		exit 1; \
	fi
