#!/usr/bin/env python3
"""
Start a daily brainstorming session issue.
Mentions @codex, /gemini, and labels for Amazon Q.
"""

import os
import sys
import datetime
import requests
import argparse

def create_brainstorm_issue(owner: str, repo: str, token: str):
    headers = {
        'Authorization': f'token {token}',
        'Accept': 'application/vnd.github+json',
        'X-GitHub-Api-Version': '2022-11-28'
    }

    date_str = datetime.date.today().isoformat()
    title = f"Daily AI Brainstorming Session - {date_str}"

    body = """
# 🧠 Daily AI Brainstorming Session

Calling all agents for a daily sync on organization improvements!

**Participants:**
- @codex (GitHub Copilot)
- Amazon Q (via labels)
- Gemini (via command)

**Topic:**
Review recent activity, open PRs, and suggest architectural improvements or automation ideas for the P4X-ng organization.

/gemini brainstorm
@codex what improvements can we make today?
    """

    # Add labels to trigger Amazon Q
    labels = ['Amazon Q development agent', 'brainstorming']

    url = f'https://api.github.com/repos/{owner}/{repo}/issues'
    data = {
        'title': title,
        'body': body.strip(),
        'labels': labels
    }

    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 201:
        print(f"✅ Created issue: {response.json()['html_url']}")
    else:
        print(f"❌ Failed to create issue: {response.text}")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--token')
    parser.add_argument('--repo', default='P4X-ng/.github')
    args = parser.parse_args()

    token = args.token or os.environ.get('GITHUB_TOKEN')
    if not token:
        sys.exit(1)

    if '/' in args.repo:
        owner, name = args.repo.split('/')
    else:
        print("Repo must be owner/name")
        sys.exit(1)

    create_brainstorm_issue(owner, name, token)

if __name__ == '__main__':
    main()
