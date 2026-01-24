#!/usr/bin/env python3
"""
Trigger a workflow across all repositories in a GitHub organization or user account.

This script uses the GitHub API to:
1. List all repositories in an organization or user account (including private repos)
2. Trigger a specified workflow in each repository
3. Report success/failure for each repository

Special feature: --all-accounts flag processes P4X-ng, HyperionGray, TeamHG-Memex, and hyp3ri0n-ng
in a single run, perfect for managing workflows across multiple accounts.

Requirements:
- GitHub token with 'repo' and 'workflow' scopes (+ 'read:org' for organizations)
- Set via GITHUB_TOKEN environment variable or --token argument
"""

import os
import sys
import argparse
import time
import requests
from typing import List, Dict, Any


def alternate_workflow_filename(workflow: str) -> str | None:
    if workflow.endswith(".yml"):
        return workflow[:-4] + ".yaml"
    if workflow.endswith(".yaml"):
        return workflow[:-5] + ".yml"
    return None


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

    if response.status_code == 200:
        return True

    if response.status_code == 404:
        alternate = alternate_workflow_filename(workflow)
        if alternate:
            url = f'https://api.github.com/repos/{owner}/{repo}/actions/workflows/{alternate}'
            response = requests.get(url, headers=headers)
            return response.status_code == 200

    return False


def trigger_workflow(owner: str, repo: str, workflow: str, ref: str, 
                     inputs: Dict[str, str], token: str) -> tuple[bool, str]:
    """
    Trigger a workflow in a repository.
    
    Args:
        owner: Repository owner
        repo: Repository name
        workflow: Workflow file name or ID
        ref: Git reference (branch, tag, or commit SHA)
        inputs: Workflow inputs
        token: GitHub token
        
    Returns:
        Tuple of (success: bool, message: str)
    """
    headers = {
        'Authorization': f'token {token}',
        'Accept': 'application/vnd.github+json',
        'X-GitHub-Api-Version': '2022-11-28'
    }
    
    url = f'https://api.github.com/repos/{owner}/{repo}/actions/workflows/{workflow}/dispatches'
    
    data = {
        'ref': ref
    }
    
    if inputs:
        data['inputs'] = inputs
    
    response = requests.post(url, headers=headers, json=data)
    
    if response.status_code == 204:
        return True, "Success"
    elif response.status_code == 404:
        alternate = alternate_workflow_filename(workflow)
        if alternate:
            url = f'https://api.github.com/repos/{owner}/{repo}/actions/workflows/{alternate}/dispatches'
            response = requests.post(url, headers=headers, json=data)
            if response.status_code == 204:
                return True, f"Success (used {alternate})"
        return False, "Workflow not found"
    else:
        return False, f"Error {response.status_code}: {response.text}"


def main():
    parser = argparse.ArgumentParser(
        description='Trigger a workflow across all repositories in an organization',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Trigger workflows-sync.yml on all repos
  python trigger_workflow_all_repos.py P4X-ng workflows-sync.yml
  
  # Trigger across all accounts (P4X-ng + HyperionGray + TeamHG-Memex)
  python trigger_workflow_all_repos.py workflows-sync.yml --all-accounts
  
  # Trigger with specific branch
  python trigger_workflow_all_repos.py P4X-ng security-scan.yml --ref main
  
  # Trigger with inputs
  python trigger_workflow_all_repos.py P4X-ng deploy.yml --input environment=production
  
  # Include archived repositories
  python trigger_workflow_all_repos.py P4X-ng test.yml --include-archived
  
  # Check only (don't trigger)
  python trigger_workflow_all_repos.py P4X-ng test.yml --check-only

Required token scopes:
  - repo (for private repositories)
  - workflow (to trigger workflows)
  - read:org (to list organization repositories)
        """
    )
    
    parser.add_argument('org', nargs='?', help='Organization or user name (not needed with --all-accounts)')
    parser.add_argument('workflow', help='Workflow file name (e.g., workflows-sync.yml)')
    parser.add_argument('--all-accounts', action='store_true',
                       help='Process all accounts: P4X-ng, HyperionGray, TeamHG-Memex, and hyp3ri0n-ng')
    parser.add_argument('--ref', default='main', help='Git reference (branch/tag/SHA, default: main)')
    parser.add_argument('--token', help='GitHub token (or set GITHUB_TOKEN env var)')
    parser.add_argument('--input', action='append', dest='inputs', 
                       help='Workflow input in key=value format (can be used multiple times)')
    parser.add_argument('--include-archived', action='store_true',
                       help='Include archived repositories')
    parser.add_argument('--check-only', action='store_true',
                       help='Only check which repos have the workflow, do not trigger')
    parser.add_argument('--delay', type=float, default=1.0,
                       help='Delay in seconds between API calls (default: 1.0)')
    
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
    
    # Parse inputs
    workflow_inputs = {}
    if args.inputs:
        for input_str in args.inputs:
            if '=' not in input_str:
                print(f"Error: Invalid input format '{input_str}'. Use key=value")
                sys.exit(1)
            key, value = input_str.split('=', 1)
            workflow_inputs[key] = value
    
    # Process each account
    total_success = 0
    total_not_found = 0
    total_error = 0
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
        
        if args.check_only:
            print(f"Checking which repositories have workflow '{args.workflow}':")
            print("-" * 80)
        else:
            print(f"Triggering workflow '{args.workflow}' on ref '{args.ref}':")
            print("-" * 80)
        
        success_count = 0
        not_found_count = 0
        error_count = 0
        
        for repo in repos:
            repo_name = repo['name']
            repo_full = repo['full_name']
            
            # Check if workflow exists
            if not workflow_exists(account, repo_name, args.workflow, token):
                print(f"⊘ {repo_full:40s} - Workflow not found")
                not_found_count += 1
                time.sleep(args.delay)
                continue
            
            if args.check_only:
                print(f"✓ {repo_full:40s} - Workflow exists")
                success_count += 1
                time.sleep(args.delay)
                continue
            
            # Trigger workflow
            success, message = trigger_workflow(
                account, repo_name, args.workflow, args.ref, workflow_inputs, token
            )
            
            if success:
                print(f"✓ {repo_full:40s} - Triggered")
                success_count += 1
            else:
                print(f"✗ {repo_full:40s} - {message}")
                error_count += 1
            
            # Rate limiting - be nice to the API
            time.sleep(args.delay)
        
        print()
        print("-" * 80)
        print(f"Summary for {account}:")
        print(f"  Total repositories: {len(repos)}")
        if args.check_only:
            print(f"  Workflow exists:    {success_count}")
        else:
            print(f"  Successfully triggered: {success_count}")
            print(f"  Errors:                {error_count}")
        print(f"  Workflow not found:     {not_found_count}")
        print()
        
        total_repos += len(repos)
        total_success += success_count
        total_not_found += not_found_count
        total_error += error_count
    
    # Print overall summary if multiple accounts
    if len(accounts) > 1:
        print()
        print("=" * 80)
        print(f"OVERALL SUMMARY (all {len(accounts)} accounts):")
        print("=" * 80)
        print(f"  Total repositories: {total_repos}")
        if args.check_only:
            print(f"  Workflow exists:    {total_success}")
        else:
            print(f"  Successfully triggered: {total_success}")
            print(f"  Errors:                {total_error}")
        print(f"  Workflow not found:     {total_not_found}")


if __name__ == '__main__':
    main()
