#!/usr/bin/env python3
"""
Trigger the auto-assign-copilot workflow across all repositories.

This script uses the GitHub API to trigger the auto-assign-copilot.yml workflow
in all repositories where it exists. Since the workflow runs on issue events,
this script is primarily for validation and can be used to manually dispatch
the workflow if needed.

For the workflow to actually trigger automatically, it needs to be:
1. Present in each repository's .github/workflows/ directory
2. An issue must be opened or labeled with 'copilot'

This script helps you:
- Check which repos have the workflow
- Optionally trigger workflow_dispatch events (if the workflow supports it)
- Report on deployment status

Requirements:
- GitHub token with 'repo' and 'workflow' scopes
- Set via GITHUB_TOKEN environment variable or --token argument

Usage:
    # Check which repos have the workflow
    python trigger_auto_assign_copilot.py --check-only
    
    # Check specific organization
    python trigger_auto_assign_copilot.py P4X-ng --check-only
    
    # Check across all accounts
    python trigger_auto_assign_copilot.py --all-accounts --check-only
"""

import os
import sys
import argparse
import time
import requests
from typing import List, Dict, Any


def get_all_repos(org: str, token: str, include_archived: bool = False) -> List[Dict[str, Any]]:
    """
    Fetch all repositories in an organization, including private ones.
    
    Args:
        org: Organization name
        token: GitHub personal access token with read:org scope
        include_archived: Whether to include archived repositories
        
    Returns:
        List of repository objects
    """
    headers = {
        'Authorization': f'token {token}',
        'Accept': 'application/vnd.github+json',
        'X-GitHub-Api-Version': '2022-11-28'
    }
    
    repos = []
    page = 1
    per_page = 100
    
    while True:
        url = f'https://api.github.com/orgs/{org}/repos'
        params = {
            'per_page': per_page,
            'page': page,
            'type': 'all'  # Get all repos (public, private, internal)
        }
        
        response = requests.get(url, headers=headers, params=params)
        
        if response.status_code == 404:
            # Try as a user account instead of org
            url = f'https://api.github.com/users/{org}/repos'
            response = requests.get(url, headers=headers, params=params)
        
        if response.status_code != 200:
            print(f"Error fetching repositories: {response.status_code}")
            print(f"Response: {response.text}")
            sys.exit(1)
        
        batch = response.json()
        if not batch:
            break
            
        repos.extend(batch)
        page += 1
        
        # Check if there are more pages
        if len(batch) < per_page:
            break
    
    # Filter out archived repos if requested
    if not include_archived:
        repos = [r for r in repos if not r.get('archived', False)]
    
    return repos


def workflow_exists(owner: str, repo: str, workflow: str, token: str) -> bool:
    """
    Check if a workflow file exists in a repository.
    
    Args:
        owner: Repository owner
        repo: Repository name
        workflow: Workflow file name or ID
        token: GitHub token
        
    Returns:
        True if workflow exists, False otherwise
    """
    headers = {
        'Authorization': f'token {token}',
        'Accept': 'application/vnd.github+json',
        'X-GitHub-Api-Version': '2022-11-28'
    }
    
    url = f'https://api.github.com/repos/{owner}/{repo}/actions/workflows/{workflow}'
    response = requests.get(url, headers=headers)
    
    return response.status_code == 200


def get_repo_labels(owner: str, repo: str, token: str) -> List[str]:
    """
    Get all labels in a repository.
    
    Args:
        owner: Repository owner
        repo: Repository name
        token: GitHub token
        
    Returns:
        List of label names
    """
    headers = {
        'Authorization': f'token {token}',
        'Accept': 'application/vnd.github+json',
        'X-GitHub-Api-Version': '2022-11-28'
    }
    
    url = f'https://api.github.com/repos/{owner}/{repo}/labels'
    params = {'per_page': 100}
    
    response = requests.get(url, headers=headers, params=params)
    
    if response.status_code == 200:
        labels = response.json()
        return [label['name'] for label in labels]
    
    return []


def main():
    parser = argparse.ArgumentParser(
        description='Check or trigger auto-assign-copilot workflow across repositories',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Check which repos have the workflow
  python trigger_auto_assign_copilot.py P4X-ng --check-only
  
  # Check across all accounts
  python trigger_auto_assign_copilot.py --all-accounts --check-only
  
  # Check and show label status
  python trigger_auto_assign_copilot.py P4X-ng --check-labels

Note:
  This workflow runs automatically on issue events (opened, labeled).
  This script is primarily for checking deployment status.
  To test the workflow, open an issue and add the 'copilot' label.

Required token scopes:
  - repo (for private repositories)
  - read:org (to list organization repositories)
        """
    )
    
    parser.add_argument('org', nargs='?', help='Organization or user name (not needed with --all-accounts)')
    parser.add_argument('--all-accounts', action='store_true',
                       help='Process all accounts: P4X-ng, HyperionGray, TeamHG-Memex, and hyp3ri0n-ng')
    parser.add_argument('--token', help='GitHub token (or set GITHUB_TOKEN env var)')
    parser.add_argument('--include-archived', action='store_true',
                       help='Include archived repositories')
    parser.add_argument('--check-only', action='store_true', default=True,
                       help='Only check which repos have the workflow (default)')
    parser.add_argument('--check-labels', action='store_true',
                       help='Also check if required labels exist in repos')
    parser.add_argument('--delay', type=float, default=0.5,
                       help='Delay in seconds between API calls (default: 0.5)')
    
    args = parser.parse_args()
    
    # Validate arguments
    if args.all_accounts and args.org:
        print("Error: Cannot specify both org and --all-accounts")
        sys.exit(1)
    
    if not args.all_accounts and not args.org:
        print("Error: Must specify either org or --all-accounts")
        sys.exit(1)
    
    # Define accounts to process
    if args.all_accounts:
        accounts = ['P4X-ng', 'HyperionGray', 'TeamHG-Memex', 'hyp3ri0n-ng']
    else:
        accounts = [args.org]
    
    # Get token
    token = args.token or os.environ.get('GITHUB_TOKEN') or os.environ.get('GH_TOKEN')
    if not token:
        print("Error: GitHub token required. Set GITHUB_TOKEN env var or use --token")
        sys.exit(1)
    
    workflow_name = 'auto-assign-copilot.yml'
    required_labels = ['copilot', 'copilot-gpt-5.1-codex', 'copilot-gpt-5.1', 'copilot-claude-4.5-opus']
    
    # Process each account
    total_has_workflow = 0
    total_missing_workflow = 0
    total_repos = 0
    
    for account in accounts:
        if len(accounts) > 1:
            print("=" * 80)
            print(f"Processing account: {account}")
            print("=" * 80)
        
        print(f"Fetching repositories for {account}...")
        repos = get_all_repos(account, token, args.include_archived)
        
        print(f"Found {len(repos)} repositories")
        print()
        print(f"Checking for workflow '{workflow_name}':")
        print("-" * 80)
        
        has_workflow = 0
        missing_workflow = 0
        
        for repo in repos:
            repo_name = repo['name']
            repo_full = repo['full_name']
            
            # Check if workflow exists
            has_wf = workflow_exists(account, repo_name, workflow_name, token)
            
            if has_wf:
                status = "✓ Has workflow"
                has_workflow += 1
                
                # Check labels if requested
                if args.check_labels:
                    labels = get_repo_labels(account, repo_name, token)
                    missing_labels = [l for l in required_labels if l not in labels]
                    
                    if missing_labels:
                        status += f" (missing labels: {', '.join(missing_labels)})"
                    else:
                        status += " (all labels present)"
                
                print(f"  {repo_full:40s} - {status}")
            else:
                print(f"  {repo_full:40s} - ⊘ Workflow not found")
                missing_workflow += 1
            
            time.sleep(args.delay)
        
        print()
        print("-" * 80)
        print(f"Summary for {account}:")
        print(f"  Total repositories:    {len(repos)}")
        print(f"  Has workflow:          {has_workflow}")
        print(f"  Missing workflow:      {missing_workflow}")
        print()
        
        total_repos += len(repos)
        total_has_workflow += has_workflow
        total_missing_workflow += missing_workflow
    
    # Print overall summary if multiple accounts
    if len(accounts) > 1:
        print()
        print("=" * 80)
        print(f"OVERALL SUMMARY (all {len(accounts)} accounts):")
        print("=" * 80)
        print(f"  Total repositories:    {total_repos}")
        print(f"  Has workflow:          {total_has_workflow}")
        print(f"  Missing workflow:      {total_missing_workflow}")
        print()
    
    print()
    print("💡 To deploy this workflow to all repos, use the workflows-sync mechanism:")
    print("   1. The workflow is in workflow-templates/auto-assign-copilot.yml")
    print("   2. Run: python trigger_workflow_all_repos.py --all-accounts workflows-sync.yml")
    print()
    print("💡 To test the workflow in a repo:")
    print("   1. Open a new issue")
    print("   2. Add the 'copilot' label")
    print("   3. The workflow will auto-assign @copilot and create model selection labels")


if __name__ == '__main__':
    main()
