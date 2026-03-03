#!/usr/bin/env bash
# Script to bulk-assign 'copilot' label to all open issues
# This will trigger the auto-assign-copilot.yml workflow to assign the Copilot user

set -euo pipefail

REPO_OWNER="${REPO_OWNER:-P4X-ng}"
REPO_NAME="${REPO_NAME:-pf-web-poly-compile-helper-runner}"
GITHUB_TOKEN="${GITHUB_TOKEN:-}"

if [[ -z "$GITHUB_TOKEN" ]]; then
    echo "Error: GITHUB_TOKEN environment variable is required"
    echo "Usage: GITHUB_TOKEN=ghp_your_token ./scripts/assign-issues-to-copilot.sh"
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
