SHELL := /bin/bash

# Repo-root venv (one directory up from pf-runner/)
REPO_VENV_PY := $(abspath ..)/.venv/bin/python

PF_ENTRY := pf_main.py
PF_LINK := pf

.PHONY: help local-install local_install link shebang test clean distclean

help:
	@echo "Targets:"
	@echo "  local-install  - create repo-local './pf' shim (uses repo .venv when available)"
	@echo "  link           - same as local-install"
	@echo "  test           - smoke test (pf help + list)"
	@echo "  clean          - remove __pycache__ and *.pyc"
	@echo "  distclean      - clean + remove local shim"

shebang:
	@# Prefer the repo-root virtualenv if present so running via symlink works.
	@if [ -x "$(REPO_VENV_PY)" ]; then \
	  sed -i '1s|^#!.*$$|#!$(REPO_VENV_PY)|' "$(PF_ENTRY)"; \
	fi
	@chmod +x "$(PF_ENTRY)"

link: shebang
	@ln -sfn ./$(PF_ENTRY) $(PF_LINK)
	@ls -l $(PF_LINK)

local-install: link

local_install: link

test: link
	@./$(PF_LINK) --help >/dev/null
	@cd .. && ./pf-runner/$(PF_LINK) list >/dev/null
	@echo "✅ pf shim ok"

clean:
	@find . -type d -name __pycache__ -prune -exec rm -rf {} + || true
	@find . -type f -name '*.pyc' -delete || true

distclean: clean
	@rm -f $(PF_LINK)
	@echo "Removed local pf shim"
