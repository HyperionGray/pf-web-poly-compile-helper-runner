#!/usr/bin/env python3
"""
Distribute issues to repositories based on a JSON/JSONL file.

Usage:
  python distribute_issues.py --file issues_batch.json --token $GITHUB_TOKEN

File Format (JSON or JSONL):
  {
    "P4X-ng/repo-name": {
      "issue": {
        "title": "Issue Title",
        "body": "Issue Body",
        "assignees": ["copilot", "user"]
      }
    },
    "ALL": {
      "issue": [
        {
          "title": "Global Issue",
          "body": "This goes to all repos"
        }
      ]
    }
  }
"""

import json
import os
import sys
import argparse
import time
import requests
from typing import List, Dict, Any, Union

# Import get_all_repos from sync_workflows
try:
    from sync_workflows import get_all_repos
except ImportError:
    # Fallback if sync_workflows.py is not in path or has issues
    print("Warning: Could not import get_all_repos from sync_workflows.py. Defining fallback.")
    def get_all_repos(owner: str, token: str, include_archived: bool = False) -> List[Dict[str, Any]]:
        # This is a simplified version of the one in sync_workflows.py
        headers = {
            'Authorization': f'token {token}',
            'Accept': 'application/vnd.github+json',
            'X-GitHub-Api-Version': '2022-11-28'
        }
        repos = []
        page = 1
        while True:
            url = f'https://api.github.com/users/{owner}/repos?per_page=100&page={page}&type=all'
            response = requests.get(url, headers=headers)
            if response.status_code != 200:
                break
            batch = response.json()
            if not batch:
                break
            repos.extend(batch)
            page += 1

        if not include_archived:
            repos = [r for r in repos if not r.get('archived', False)]
        return [r for r in repos if r['name'] != '.github']

def load_issues_file(filepath: str) -> Dict[str, Any]:
    """Load issues from a JSON or JSONL file."""
    if not os.path.exists(filepath):
        print(f"❌ Error: File '{filepath}' not found")
        sys.exit(1)

    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read().strip()

    # Try parsing as standard JSON
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        pass

    # Try parsing as JSONL (line-delimited JSON)
    data = {}
    lines = content.split('\n')
    for line in lines:
        line = line.strip()
        if not line:
            continue
        try:
            entry = json.loads(line)
            # Merge entry into data
            for k, v in entry.items():
                if k in data:
                    # If key exists, convert to list or append
                    if isinstance(data[k], list):
                        data[k].append(v)
                    else:
                        data[k] = [data[k], v]
                else:
                    data[k] = v
        except json.JSONDecodeError as e:
            print(f"❌ Error parsing JSONL line: {e}")
            sys.exit(1)

    return data

def get_open_issues(owner: str, repo: str, token: str) -> List[Dict[str, Any]]:
    """Get all open issues for a repository to check for duplicates."""
    headers = {
        'Authorization': f'token {token}',
        'Accept': 'application/vnd.github+json',
        'X-GitHub-Api-Version': '2022-11-28'
    }

    issues = []
    page = 1
    while True:
        url = f'https://api.github.com/repos/{owner}/{repo}/issues'
        params = {'state': 'open', 'per_page': 100, 'page': page}
        response = requests.get(url, headers=headers, params=params)

        if response.status_code != 200:
            print(f"   ⚠️ Could not fetch issues for {owner}/{repo}: {response.status_code}")
            return []

        batch = response.json()
        if not batch:
            break

        issues.extend(batch)
        page += 1

    return issues

def create_issue(owner: str, repo: str, issue_data: Dict[str, Any], token: str, dry_run: bool = False) -> bool:
    """Create an issue in the specified repository."""
    headers = {
        'Authorization': f'token {token}',
        'Accept': 'application/vnd.github+json',
        'X-GitHub-Api-Version': '2022-11-28'
    }

    title = issue_data.get('title')
    body = issue_data.get('body', '')
    assignees = issue_data.get('assignees', [])
    labels = issue_data.get('labels', [])

    if not title:
        print(f"   ⚠️ Skipping issue with no title")
        return False

    # GitHub API does not allow assigning 'copilot' directly.
    # We must use a label (e.g., 'copilot') to trigger a workflow that assigns it.
    final_assignees = []
    final_labels = list(labels)

    for assignee in assignees:
        if assignee.lower() == 'copilot':
            if 'copilot' not in final_labels:
                final_labels.append('copilot')
        else:
            final_assignees.append(assignee)

    # If the user wants ALL bulk issues to be handled by Copilot (implied by context),
    # we can enforce the label here, but for now we'll stick to explicit intent.

    if dry_run:
        print(f"   [DRY RUN] Would create issue: '{title}' in {owner}/{repo}")
        print(f"             Assignees: {final_assignees}, Labels: {final_labels}")
        return True

    url = f'https://api.github.com/repos/{owner}/{repo}/issues'
    payload = {
        'title': title,
        'body': body,
        'assignees': final_assignees,
        'labels': final_labels
    }

    response = requests.post(url, headers=headers, json=payload)

    if response.status_code == 201:
        issue_num = response.json().get('number')
        print(f"   ✅ Created issue #{issue_num}: '{title}'")
        return True
    else:
        print(f"   ❌ Failed to create issue: {response.status_code}")
        print(f"      {response.text}")
        return False

def process_target(target_key: str, data: Any, all_repos: List[Dict[str, Any]], token: str, dry_run: bool):
    """Process a single target key (specific repo or ALL) and its issue data."""

    # Determine target repositories
    targets = []
    if target_key in ['ALL', '*', 'all']:
        targets = all_repos
    elif target_key.endswith('/*'):
        # Handle "Owner/*" wildcard
        owner_filter = target_key.split('/')[0]
        targets = [r for r in all_repos if r['owner']['login'] == owner_filter]
    else:
        # Specific repository "Owner/Repo"
        if '/' in target_key:
            owner, name = target_key.split('/')
            targets = [{'name': name, 'owner': {'login': owner}}]
        else:
            # Assume it's just a repo name under the default owner (if we had one, but we don't strictly)
            # Ideally we need full name. We'll search in all_repos for a match.
            matches = [r for r in all_repos if r['name'] == target_key]
            if matches:
                targets = matches
            else:
                print(f"⚠️ Repository not found: {target_key}")
                return

    # Extract issue list
    issue_list = []
    if isinstance(data, dict) and 'issue' in data:
        item = data['issue']
        if isinstance(item, list):
            issue_list = item
        else:
            issue_list = [item]
    elif isinstance(data, list):
        # Maybe the value is directly a list of issues
        issue_list = data
    else:
        # Maybe the value is directly an issue object
        issue_list = [data]

    print(f"🎯 Target: {target_key} -> {len(targets)} repositories")

    for repo in targets:
        owner = repo['owner']['login']
        name = repo['name']
        full_name = f"{owner}/{name}"

        print(f"   Processing {full_name}...")

        # specific_issues = get_open_issues(owner, name, token)
        # existing_titles = {i['title'] for i in specific_issues}

        # Optimization: Fetch issues only if we are going to create something
        existing_titles = None

        for issue_def in issue_list:
            title = issue_def.get('title')
            if not title:
                continue

            # Lazy load existing issues to avoid API calls if list is empty
            if existing_titles is None:
                 existing_issues = get_open_issues(owner, name, token)
                 existing_titles = {i['title'] for i in existing_issues}

            if title in existing_titles:
                print(f"   ℹ️ Issue already exists: '{title}'")
                continue

            create_issue(owner, name, issue_def, token, dry_run)
            time.sleep(1) # Rate limit friendly

def main():
    parser = argparse.ArgumentParser(description='Distribute issues to repositories')
    parser.add_argument('--file', default='issues_batch.json', help='Path to JSON/JSONL file with issues')
    parser.add_argument('--token', help='GitHub Token')
    parser.add_argument('--dry-run', action='store_true', help='Simulate without creating issues')
    parser.add_argument('--owner', default='P4X-ng', help='Default owner for fetching ALL repos')
    parser.add_argument('--all-accounts', action='store_true', help='Scan P4X-ng, HyperionGray, and TeamHG-Memex')

    args = parser.parse_args()

    token = args.token or os.environ.get('GITHUB_TOKEN')
    if not token:
        print("❌ Error: GitHub token required")
        sys.exit(1)

    print(f"📂 Loading issues from {args.file}...")
    data = load_issues_file(args.file)

    all_repos = []
    if args.all_accounts:
        accounts = ['P4X-ng', 'HyperionGray', 'TeamHG-Memex']
        print(f"🔍 Fetching repositories for accounts: {', '.join(accounts)}...")
        for account in accounts:
            print(f"   - Fetching {account}...")
            all_repos.extend(get_all_repos(account, token))
    else:
        print(f"🔍 Fetching repository list for {args.owner}...")
        all_repos = get_all_repos(args.owner, token)

    print(f"📦 Found {len(all_repos)} repositories available for wildcard targets")

    for target_key, issue_data in data.items():
        process_target(target_key, issue_data, all_repos, token, args.dry_run)

    print("\n✨ Done")

if __name__ == '__main__':
    main()
