#!/bin/bash
grep -r "austenstone/copilot-cli-action" .github/workflows/ || echo "No remaining references found"