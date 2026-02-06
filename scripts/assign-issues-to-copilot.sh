#!/usr/bin/env bash
# Script to bulk-assign 'copilot' label to all open issues
# This will trigger the auto-assign-copilot.yml workflow to assign the Copilot user

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

PROJECT_CONFIG="${REPO_ROOT}/pf.config.json5"
USER_CONFIG=""
if [[ -n "${HOME:-}" ]]; then
    [[ -f "${HOME}/.config/pf/pf.config.json5" ]] && USER_CONFIG="${HOME}/.config/pf/pf.config.json5"
    [[ -z "${USER_CONFIG}" && -f "${HOME}/.pf/pf.config.json5" ]] && USER_CONFIG="${HOME}/.pf/pf.config.json5"
fi

json5_get() {
    local cfg_path="$1"
    local dotted_key="$2"
    local default="$3"

    if [[ -z "${cfg_path}" || ! -f "${cfg_path}" ]]; then
        echo "$default"
        return 0
    fi
    if ! command -v python3 >/dev/null 2>&1; then
        echo "$default"
        return 0
    fi

    python3 - "$cfg_path" "$dotted_key" "$default" <<'PY' 2>/dev/null || echo "$default"
import sys

cfg_path = sys.argv[1]
key = sys.argv[2]
default = sys.argv[3]

try:
    import json5  # type: ignore
except Exception:
    print(default)
    raise SystemExit(0)

try:
    with open(cfg_path, "r", encoding="utf-8") as f:
        data = json5.load(f)
except Exception:
    print(default)
    raise SystemExit(0)

cur = data
for part in key.split("."):
    if not isinstance(cur, dict) or part not in cur:
        print(default)
        raise SystemExit(0)
    cur = cur[part]

if cur is None:
    print(default)
elif isinstance(cur, bool):
    print("true" if cur else "false")
else:
    print(str(cur))
PY
}

cfg_get() {
    local dotted_key="$1"
    local default="$2"

    local v=""
    if [[ -n "${USER_CONFIG}" ]]; then
        v="$(json5_get "${USER_CONFIG}" "$dotted_key" "")"
    fi
    if [[ -z "${v}" ]]; then
        v="$(json5_get "${PROJECT_CONFIG}" "$dotted_key" "$default")"
    fi
    echo "$v"
}

detect_repo_from_git() {
    if ! command -v git >/dev/null 2>&1; then
        return 0
    fi

    local remote_url=""
    remote_url="$(git -C "${REPO_ROOT}" remote get-url origin 2>/dev/null || true)"
    if [[ -z "${remote_url}" ]]; then
        return 0
    fi

    # Match: git@github.com:owner/name(.git) or https://github.com/owner/name(.git)
    if [[ "${remote_url}" =~ github\.com[:/]+([^/]+)/([^/]+)(\.git)?$ ]]; then
        echo "${BASH_REMATCH[1]} ${BASH_REMATCH[2]}"
        return 0
    fi
    return 0
}

REPO_OWNER="$(cfg_get "github.repoOwner" "")"
REPO_NAME="$(cfg_get "github.repoName" "")"
GITHUB_TOKEN="$(cfg_get "github.token" "")"

if [[ -z "${REPO_OWNER}" || -z "${REPO_NAME}" ]]; then
    if git_guess="$(detect_repo_from_git)"; then
        if [[ -n "${git_guess}" ]]; then
            REPO_OWNER="${REPO_OWNER:-${git_guess%% *}}"
            REPO_NAME="${REPO_NAME:-${git_guess##* }}"
        fi
    fi
fi

if [[ -z "${REPO_OWNER}" || -z "${REPO_NAME}" ]]; then
    echo "Error: GitHub repo not configured."
    echo "Set github.repoOwner and github.repoName in pf.config.json5."
    exit 1
fi

if [[ -z "$GITHUB_TOKEN" ]]; then
    echo "Error: GitHub token is required."
    echo "Set github.token in ~/.config/pf/pf.config.json5 (preferred) or ${PROJECT_CONFIG}"
    exit 1
fi

echo "Fetching open issues from ${REPO_OWNER}/${REPO_NAME}..."

# Fetch all open issues (with pagination support)
page=1
all_issues="[]"

while true; do
    echo "  Fetching page $page..."
    issues_json=$(curl -s -H "Authorization: token $GITHUB_TOKEN" \
        "https://api.github.com/repos/${REPO_OWNER}/${REPO_NAME}/issues?state=open&per_page=100&page=$page")
    
    # Check if we got valid JSON
    if ! echo "$issues_json" | jq empty 2>/dev/null; then
        echo "Error: Failed to fetch issues or invalid JSON response"
        echo "Response: $issues_json"
        exit 1
    fi
    
    # Check if this page has any issues
    page_count=$(echo "$issues_json" | jq 'length')
    if [[ $page_count -eq 0 ]]; then
        break
    fi
    
    # Merge with all issues
    all_issues=$(echo "$all_issues" "$issues_json" | jq -s 'add')
    
    # If we got less than 100 results, we're done
    if [[ $page_count -lt 100 ]]; then
        break
    fi
    
    ((page++))
done

issues_json="$all_issues"

# Count total open issues
total_issues=$(echo "$issues_json" | jq 'length')
echo "Found $total_issues open issues"

if [[ $total_issues -eq 0 ]]; then
    echo "No open issues found. Nothing to do."
    exit 0
fi

# Process each issue
issues_updated=0
issues_already_labeled=0
issues_skipped=0

while read -r issue_number; do
    # Get issue details
    issue_data=$(echo "$issues_json" | jq ".[] | select(.number == $issue_number)")
    issue_title=$(echo "$issue_data" | jq -r '.title')
    
    # Check if issue is a pull request (skip PRs)
    if echo "$issue_data" | jq -e '.pull_request' > /dev/null 2>&1; then
        echo "  Issue #$issue_number: Skipping (is a pull request)"
        ((issues_skipped++))
        continue
    fi
    
    # Check if 'copilot' label already exists
    has_copilot_label=$(echo "$issue_data" | jq '[.labels[].name] | contains(["copilot"])')
    
    if [[ "$has_copilot_label" == "true" ]]; then
        echo "  Issue #$issue_number: Already has 'copilot' label"
        ((issues_already_labeled++))
    else
        echo "  Issue #$issue_number: Adding 'copilot' label - \"$issue_title\""
        
        # Add the copilot label
        response=$(curl -s -X POST \
            -H "Authorization: token $GITHUB_TOKEN" \
            -H "Accept: application/vnd.github.v3+json" \
            "https://api.github.com/repos/${REPO_OWNER}/${REPO_NAME}/issues/${issue_number}/labels" \
            -d "{\"labels\":[\"copilot\"]}")
        
        if echo "$response" | jq -e '.[]' > /dev/null 2>&1; then
            echo "    ✅ Successfully added 'copilot' label"
            ((issues_updated++))
            # Wait a bit to avoid rate limiting
            sleep 1
        else
            echo "    ❌ Failed to add label. Response: $response"
        fi
    fi
done < <(echo "$issues_json" | jq -r '.[].number')

echo ""
echo "Summary:"
echo "  Total issues processed: $total_issues"
echo "  Issues updated: $issues_updated"
echo "  Issues already labeled: $issues_already_labeled"
echo "  Issues skipped (PRs): $issues_skipped"
echo ""
echo "Note: The auto-assign-copilot.yml workflow will automatically assign"
echo "the Copilot user to issues with the 'copilot' label."
