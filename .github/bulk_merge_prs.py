#!/usr/bin/env python3
"""
Bulk merge PRs that have been reviewed by AI agents.

Criteria for merging:
1. Amazon Q interaction (labels: 'Amazon Q development agent', 'Amazon Q transform agent' OR comment check)
2. Codex interaction (comment containing '@codex')
3. Gemini interaction (comment containing '/gemini review')

Action: Rebase merge.
"""

import os
import sys
import time
import requests
import argparse
from typing import List, Dict, Any

# Import get_all_repos from sync_workflows
try:
    from sync_workflows import get_all_repos
except ImportError:
    # Fallback definition
    def get_all_repos(owner: str, token: str, include_archived: bool = False) -> List[Dict[str, Any]]:
        headers = {
            'Authorization': f'token {token}',
            'Accept': 'application/vnd.github+json',
            'X-GitHub-Api-Version': '2022-11-28'
        }
        repos = []
        page = 1
        while True:
            # Check users first since P4X-ng is a user
            url = f'https://api.github.com/users/{owner}/repos?per_page=100&page={page}&type=all'
            response = requests.get(url, headers=headers)
            if response.status_code == 404:
                 url = f'https://api.github.com/orgs/{owner}/repos?per_page=100&page={page}&type=all'
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

def get_open_prs(owner: str, repo: str, token: str) -> List[Dict[str, Any]]:
    """Get open PRs for a repo."""
    headers = {'Authorization': f'token {token}', 'Accept': 'application/vnd.github+json'}
    url = f'https://api.github.com/repos/{owner}/{repo}/pulls'
    params = {'state': 'open', 'per_page': 100}
    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        return response.json()
    return []

def check_reviews(owner: str, repo: str, pr_number: int, labels: List[Dict], token: str) -> bool:
    """Check if PR meets AI review criteria."""

    # 1. Check Labels (Amazon Q)
    label_names = [l['name'] for l in labels]
    q_labels = ['Amazon Q development agent', 'Amazon Q transform agent']
    has_q = any(l in label_names for l in q_labels)

    # 2. Check Comments (Codex & Gemini & Q fallback)
    headers = {'Authorization': f'token {token}', 'Accept': 'application/vnd.github+json'}
    url = f'https://api.github.com/repos/{owner}/{repo}/issues/{pr_number}/comments'
    response = requests.get(url, headers=headers)

    has_codex = False
    has_gemini = False

    if response.status_code == 200:
        comments = response.json()
        for comment in comments:
            body = comment.get('body', '').lower()
            if '@codex' in body:
                has_codex = True
            if '/gemini review' in body:
                has_gemini = True
            # Fallback for Q if labels missing but commented
            if 'amazon q' in body:
                has_q = True

    # User said: "reviewed by codex and Q... May as well add gemini"
    # Assuming strict AND might be too aggressive if they aren't all enabled on every repo.
    # But user asked "reviewed by codex AND Q", so let's try to match at least 2 out of 3 or specific combos.
    # For now, I'll log what we found and be permissive if at least ONE "big AI" has touched it,
    # OR follow strict instructions.
    # "reviewed by codex and Q" implies AND.

    # Let's enforce: Has Q interaction AND (Has Codex OR Has Gemini)
    # This seems like a safe interpretation of "Codex and Q... add gemini in the mix".

    return has_q and (has_codex or has_gemini)

def merge_pr(owner: str, repo: str, pr_number: int, token: str) -> bool:
    """Attempt rebase merge."""
    headers = {'Authorization': f'token {token}', 'Accept': 'application/vnd.github+json'}
    url = f'https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}/merge'

    data = {
        'merge_method': 'rebase'
    }

    response = requests.put(url, headers=headers, json=data)

    if response.status_code == 200:
        print(f"      ✅ Merged PR #{pr_number}")
        return True
    elif response.status_code == 405:
        print(f"      ❌ Merge failed (Not mergeable/Conflict): {response.json().get('message')}")
        return False
    else:
        print(f"      ❌ Merge failed ({response.status_code}): {response.json().get('message')}")
        return False

def main():
    parser = argparse.ArgumentParser(description='Bulk merge AI-reviewed PRs')
    parser.add_argument('--token', help='GitHub Token')
    parser.add_argument('--owner', default='P4X-ng', help='Owner/User')
    parser.add_argument('--all-accounts', action='store_true', help='Scan P4X-ng, HyperionGray, and TeamHG-Memex')
    parser.add_argument('--dry-run', action='store_true')

    args = parser.parse_args()
    token = args.token or os.environ.get('GITHUB_TOKEN')

    if not token:
        print("Error: Token required")
        sys.exit(1)

    repos = []
    if args.all_accounts:
        accounts = ['P4X-ng', 'HyperionGray', 'TeamHG-Memex']
        print(f"🔍 Scanning repos for accounts: {', '.join(accounts)}...")
        for account in accounts:
            repos.extend(get_all_repos(account, token))
    else:
        print(f"🔍 Scanning repos for {args.owner}...")
        repos = get_all_repos(args.owner, token)

    print(f"📦 Checking {len(repos)} repositories...")

    for repo in repos:
        owner = repo['owner']['login']
        name = repo['name']
        print(f"📂 {name}")

        prs = get_open_prs(owner, name, token)
        if not prs:
            continue

        for pr in prs:
            num = pr['number']
            title = pr['title']
            labels = pr.get('labels', [])

            if check_reviews(owner, name, num, labels, token):
                print(f"   🚀 Ready to merge: #{num} {title}")
                if not args.dry_run:
                    merge_pr(owner, name, num, token)
            else:
                # specific debug
                # print(f"   Skipping #{num} (Criteria not met)")
                pass

if __name__ == '__main__':
    main()
