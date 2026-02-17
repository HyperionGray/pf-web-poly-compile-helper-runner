SHELL := /bin/bash

REPO_VENV := $(abspath .)/.venv/bin/python
PF_PY := $(shell if [ -x "$(REPO_VENV)" ]; then echo "$(REPO_VENV)"; elif command -v python3 >/dev/null 2>&1; then command -v python3; else command -v python; fi)
PIP := $(PF_PY) -m pip

PF_LINK := pf
PF_CLI := pf_universal

.PHONY: help local-install local_install link setup-venv test clean distclean

help:
	@echo "Targets:"
	@echo "  local-install  - create repo-local './pf' shim (native runner)"
	@echo "  setup-venv     - create .venv and install deps (editable)"
	@echo "  test           - smoke test pf against pf-files/tests/fixtures/test.pf"
	@echo "  clean          - remove __pycache__ and *.pyc"
	@echo "  distclean      - clean and remove the local shim"

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
	@$(PF_PY) -m pf_main -f pf-files/tests/fixtures/test.pf list

clean:
	@find . -type d -name __pycache__ -prune -exec rm -rf {} + || true
	@find . -type f -name '*.pyc' -delete || true

distclean: clean
	@rm -f $(PF_LINK)
	@echo "Removed local pf shim"
