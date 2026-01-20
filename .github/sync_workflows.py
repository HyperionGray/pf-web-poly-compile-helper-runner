#!/usr/bin/env python3
"""
Sync workflow template files from this .github repository to all other repositories.

This script:
1. Lists all repositories in the specified account(s) (including private repos)
2. For each repository, copies files from workflow-templates/ to .github/workflows/
3. Creates commits directly using the GitHub API
4. Handles file creation, updates, and optionally deletions
5. Implements proper rate limiting and error handling

Requirements:
- GitHub token with 'repo' and 'workflow' scopes
- Set via GITHUB_TOKEN environment variable or --token argument
"""

import os
import sys
import argparse
import base64
import requests
from typing import List, Dict, Any, Optional, Tuple
import time
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

class GitHubAPIClient:
    """GitHub API client with rate limiting and error handling."""
    
    def __init__(self, token: str):
        self.token = token
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'token {token}',
            'Accept': 'application/vnd.github+json',
            'X-GitHub-Api-Version': '2022-11-28'
        })
        self._rate_limit_lock = threading.Lock()
        self._last_request_time = 0
        self._min_request_interval = 0.1  # 100ms between requests
    
    def _wait_for_rate_limit(self):
        """Ensure we don't exceed rate limits."""
        with self._rate_limit_lock:
            current_time = time.time()
            time_since_last = current_time - self._last_request_time
            if time_since_last < self._min_request_interval:
                time.sleep(self._min_request_interval - time_since_last)
            self._last_request_time = time.time()
    
    def _handle_rate_limit(self, response: requests.Response) -> bool:
        """Handle rate limit responses. Returns True if request should be retried."""
        if response.status_code == 429:
            reset_time = int(response.headers.get('X-RateLimit-Reset', time.time() + 60))
            wait_time = max(reset_time - int(time.time()), 1)
            print(f"⏳ Rate limit exceeded. Waiting {wait_time} seconds...")
            time.sleep(wait_time)
            return True
        
        # Update rate limit info for future requests
        remaining = response.headers.get('X-RateLimit-Remaining')
        if remaining and int(remaining) < 100:
            # Slow down when approaching rate limit
            self._min_request_interval = 0.5
        else:
            self._min_request_interval = 0.1
        
        return False
    
    def request(self, method: str, url: str, max_retries: int = 3, **kwargs) -> requests.Response:
        """Make a request with rate limiting and retry logic."""
        for attempt in range(max_retries + 1):
            self._wait_for_rate_limit()
            
            try:
                response = self.session.request(method, url, **kwargs)
                
                if self._handle_rate_limit(response):
                    continue  # Retry after rate limit wait
                
                if response.status_code in [500, 502, 503, 504] and attempt < max_retries:
                    wait_time = 2 ** attempt  # Exponential backoff
                    print(f"⚠️  Server error {response.status_code}, retrying in {wait_time}s...")
                    time.sleep(wait_time)
                    continue
                
                return response
                
            except requests.exceptions.RequestException as e:
                if attempt < max_retries:
                    wait_time = 2 ** attempt
                    print(f"⚠️  Request failed: {e}, retrying in {wait_time}s...")
                    time.sleep(wait_time)
                    continue
                raise
        
        return response
    
    def get(self, url: str, **kwargs) -> requests.Response:
        return self.request('GET', url, **kwargs)
    
    def put(self, url: str, **kwargs) -> requests.Response:
        return self.request('PUT', url, **kwargs)


def get_all_repos(owner: str, client: GitHubAPIClient, include_archived: bool = False) -> List[Dict[str, Any]]:
    """Fetch all repositories for an owner (org or user), including private ones."""
    repos = []
    page = 1
    per_page = 100
    
    while True:
        # Try as org first
        url = f'https://api.github.com/orgs/{owner}/repos'
        params = {
            'per_page': per_page,
            'page': page,
            'type': 'all'
        }
        
        response = client.get(url, params=params)
        
        if response.status_code == 404:
            # Try as user account instead
            url = f'https://api.github.com/users/{owner}/repos'
            response = client.get(url, params=params)
        
        if response.status_code != 200:
            print(f"❌ Error fetching repositories for {owner}: {response.status_code}")
            print(f"   Response: {response.text}")
            return []
        
        batch = response.json()
        if not batch:
            break
            
        repos.extend(batch)
        page += 1
        
        if len(batch) < per_page:
            break
    
    # Filter out archived repos and the .github repo itself
    if not include_archived:
        repos = [r for r in repos if not r.get('archived', False)]
    
    repos = [r for r in repos if r['name'] != '.github']
    print(json.dumps(repos))
    
    return repos


def get_file_content(filepath: str) -> Tuple[Optional[str], Optional[str]]:
    """Read file and return content and encoding."""
    try:
        with open(filepath, 'rb') as f:
            content = f.read()
            # Try to decode as UTF-8 first
            try:
                content.decode('utf-8')
                return base64.b64encode(content).decode('utf-8'), 'base64'
            except UnicodeDecodeError:
                # Binary file
                return base64.b64encode(content).decode('utf-8'), 'base64'
    except Exception as e:
        print(f"❌ Error reading file {filepath}: {e}")
        return None, None


def get_repo_file_sha(owner: str, repo: str, path: str, client: GitHubAPIClient) -> Optional[str]:
    """Get the SHA of an existing file in a repository."""
    url = f'https://api.github.com/repos/{owner}/{repo}/contents/{path}'
    response = client.get(url)
    
    if response.status_code == 200:
        return response.json().get('sha')
    return None


def sync_file_to_repo(owner: str, repo: str, branch: str, source_path: str, dest_path: str,
                      commit_message: str, client: GitHubAPIClient) -> Tuple[bool, str]:
    """Sync a single file to a repository. Returns (success, message)."""
    # Read source file
    content, encoding = get_file_content(source_path)
    if content is None:
        return False, "Failed to read source file"
    
    # Check if file exists in target repo
    existing_sha = get_repo_file_sha(owner, repo, dest_path, client)
    
    # Prepare API request
    url = f'https://api.github.com/repos/{owner}/{repo}/contents/{dest_path}'
    data = {
        'message': commit_message,
        'content': content,
        'branch': branch
    }
    
    if existing_sha:
        data['sha'] = existing_sha
    
    response = client.put(url, json=data)
    
    if response.status_code in [200, 201]:
        return True, "Success"
    elif response.status_code == 403:
        error_msg = response.json().get('message', 'Permission denied')
        if 'push access' in error_msg.lower():
            return False, "No push access to repository"
        return False, f"Permission denied: {error_msg}"
    elif response.status_code == 404:
        return False, "Repository not found or no access"
    else:
        error_msg = response.json().get('message', 'Unknown error')
        return False, f"API error {response.status_code}: {error_msg}"


def sync_repo_files(owner: str, repo_info: Dict[str, Any], files_to_sync: List[Tuple[str, str, str]], 
                   client: GitHubAPIClient, dry_run: bool = False) -> Dict[str, Any]:
    """Sync all files to a single repository."""
    repo_name = repo_info['name']
    default_branch = repo_info.get('default_branch', 'main')
    
    result = {
        'repo': repo_name,
        'synced': 0,
        'errors': 0,
        'skipped': 0,
        'messages': []
    }
    
    if dry_run:
        result['messages'].append(f"Would sync {len(files_to_sync)} files")
        result['skipped'] = len(files_to_sync)
        return result
    
    for source_path, dest_path, filename in files_to_sync:
        commit_msg = f"Sync {filename} from .github repo"
        
        success, message = sync_file_to_repo(owner, repo_name, default_branch, 
                                           source_path, dest_path, commit_msg, client)
        
        if success:
            result['synced'] += 1
            result['messages'].append(f"✅ {filename}")
        else:
            result['errors'] += 1
            result['messages'].append(f"❌ {filename}: {message}")
            
            # If we get permission errors, likely all files will fail
            if 'permission' in message.lower() or 'access' in message.lower():
                result['messages'].append(f"   Skipping remaining files due to access issues")
                result['skipped'] = len(files_to_sync) - result['synced'] - result['errors']
                break
    
    return result


def sync_workflows(owner: str, client: GitHubAPIClient, source_dir: str = 'workflow-templates',
                  dest_dir: str = '.github/workflows', dry_run: bool = False,
                  include_archived: bool = False, max_workers: int = 5) -> bool:
    """Sync all workflow template files to all repositories.
    
    Returns:
        bool: True if sync was successful (more successes than errors), False otherwise.
    """
    
    print(f"🔍 Fetching repositories for {owner}...")
    repos = get_all_repos(owner, client, include_archived)
    print(f"📦 Found {len(repos)} repositories")
    
    if dry_run:
        print("\n🧪 DRY RUN MODE - No changes will be made\n")
    
    # Get list of files to sync
    if not os.path.exists(source_dir):
        print(f"❌ Error: Source directory '{source_dir}' not found")
        sys.exit(1)
    
    files_to_sync = []
    for root, dirs, files in os.walk(source_dir):
        # Skip hidden directories (like `.git`, `.bish`, etc.)
        dirs[:] = [d for d in dirs if not d.startswith('.')]

        for file in files:
            # Only sync workflow files. Avoid syncing template metadata, indexes, or other artifacts.
            if file.startswith('.'):
                continue
            if not (file.endswith('.yml') or file.endswith('.yaml')):
                continue
            source_path = os.path.join(root, file)
            rel_path = os.path.relpath(source_path, source_dir)
            dest_path = os.path.join(dest_dir, rel_path).replace('\\', '/')
            files_to_sync.append((source_path, dest_path, file))
    
    print(f"📄 Files to sync: {len(files_to_sync)}")
    for _, _, filename in files_to_sync:
        print(f"   - {filename}")
    
    print(f"\n{'='*60}\n")
    
    # Sync to repositories (with limited parallelism to avoid rate limits)
    total_synced = 0
    total_errors = 0
    total_skipped = 0
    
    with ThreadPoolExecutor(max_workers=min(max_workers, len(repos))) as executor:
        # Submit all sync tasks
        future_to_repo = {
            executor.submit(sync_repo_files, owner, repo, files_to_sync, client, dry_run): repo
            for repo in repos
        }
        
        # Process results as they complete
        for future in as_completed(future_to_repo):
            repo = future_to_repo[future]
            try:
                result = future.result()
                
                print(f"📂 {result['repo']}")
                for message in result['messages']:
                    print(f"   {message}")
                
                if result['synced'] > 0 or result['errors'] > 0:
                    print(f"   📊 Synced: {result['synced']}, Errors: {result['errors']}, Skipped: {result['skipped']}")
                
                total_synced += result['synced']
                total_errors += result['errors']
                total_skipped += result['skipped']
                
            except Exception as e:
                print(f"📂 {repo['name']}")
                print(f"   ❌ Unexpected error: {e}")
                total_errors += len(files_to_sync)
    
    print(f"\n{'='*60}")
    print(f"✨ Summary for {owner}:")
    print(f"   Repositories processed: {len(repos)}")
    print(f"   Files synced: {total_synced}")
    print(f"   Errors: {total_errors}")
    print(f"   Skipped: {total_skipped}")
    
    # Return success/failure status instead of exiting
    success = total_synced > total_errors or dry_run or len(repos) == 0
    
    if not success and not dry_run:
        print(f"\n⚠️  More errors than successes - check token permissions and repository access")
    
    return success


def main():
    parser = argparse.ArgumentParser(
        description='Sync workflow templates to all repositories',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Sync workflows to all P4X-ng repositories
  python sync_workflows.py P4X-ng

  # Sync workflows to all accounts (P4X-ng, HyperionGray, TeamHG-Memex, hyp3ri0n-ng)
  python sync_workflows.py --all-accounts

  # Dry run to see what would be synced
  python sync_workflows.py P4X-ng --dry-run
  
  # Include archived repositories
  python sync_workflows.py P4X-ng --include-archived

Environment Variables:
  GITHUB_TOKEN - GitHub personal access token (required if not using --token)
        """
    )
    
    parser.add_argument('owner', nargs='?', help='Repository owner (organization or user, not needed with --all-accounts)')
    parser.add_argument('--all-accounts', action='store_true',
                       help='Process all accounts: P4X-ng, HyperionGray, TeamHG-Memex, and hyp3ri0n-ng')
    parser.add_argument('--token', help='GitHub token (or use GITHUB_TOKEN env var)')
    parser.add_argument('--source-dir', default='workflow-templates',
                       help='Source directory containing workflow templates (default: workflow-templates)')
    parser.add_argument('--dest-dir', default='.github/workflows',
                       help='Destination directory in target repos (default: .github/workflows)')
    parser.add_argument('--dry-run', action='store_true',
                       help='Show what would be synced without making changes')
    parser.add_argument('--include-archived', action='store_true',
                       help='Include archived repositories')
    parser.add_argument('--max-workers', type=int, default=3,
                       help='Maximum number of concurrent repository syncs (default: 3)')
    
    args = parser.parse_args()
    
    # Validate arguments
    if args.all_accounts and args.owner:
        print("❌ Error: Cannot specify both owner and --all-accounts")
        sys.exit(1)
    
    if not args.all_accounts and not args.owner:
        print("❌ Error: Must specify either owner or --all-accounts")
        sys.exit(1)
    
    # Define accounts to process
    if args.all_accounts:
        accounts = ['P4X-ng', 'HyperionGray', 'TeamHG-Memex', 'hyp3ri0n-ng']
    else:
        accounts = [args.owner]
    
    # Get token
    token = args.token or os.environ.get('GITHUB_TOKEN')
    if not token:
        print("❌ Error: GitHub token required. Set GITHUB_TOKEN or use --token")
        print("\nToken must have these scopes:")
        print("  - repo (access repositories)")
        print("  - workflow (update workflows)")
        sys.exit(1)
    
    # Create API client
    client = GitHubAPIClient(token)
    
    # Process each account
    overall_success = True
    primary_account_success = True  # Track P4X-ng specifically
    account_results = {}  # Track results per account
    
    for i, owner in enumerate(accounts):
        if len(accounts) > 1:
            if i > 0:
                print("\n")
            print("=" * 80)
            print(f"Processing account: {owner}")
            print("=" * 80)
            print()
        
        try:
            success = sync_workflows(
                owner,
                client,
                args.source_dir,
                args.dest_dir,
                args.dry_run,
                args.include_archived,
                args.max_workers
            )
            account_results[owner] = success
            
            # Track if primary account (P4X-ng) failed
            if owner == 'P4X-ng' and not success:
                primary_account_success = False
            
            # Track overall success (at least one account succeeded)
            if not success:
                overall_success = False
                
        except Exception as e:
            print(f"❌ Unexpected error processing {owner}: {e}")
            account_results[owner] = False
            
            if owner == 'P4X-ng':
                primary_account_success = False
            overall_success = False
    
    # Print summary for multiple accounts
    if len(accounts) > 1:
        print("\n" + "=" * 80)
        print("OVERALL SUMMARY")
        print("=" * 80)
        for owner, success in account_results.items():
            status = "✅ Success" if success else "❌ Failed"
            print(f"  {owner}: {status}")
        print()
    
    # Fail only if:
    # 1. Primary account (P4X-ng) failed, OR
    # 2. All accounts failed
    all_failed = len(account_results) > 0 and all(not success for success in account_results.values())
    
    if not primary_account_success:
        print(f"\n⚠️  Primary account (P4X-ng) sync failed - this is a critical error")
        sys.exit(1)
    elif all_failed:
        print(f"\n⚠️  All accounts failed - check token permissions and repository access")
        sys.exit(1)
    elif not overall_success:
        print(f"\n⚠️  Some secondary accounts failed, but P4X-ng succeeded")
        print(f"    This is expected if the token doesn't have access to all accounts")
        # Don't exit with error - partial success is acceptable


if __name__ == '__main__':
    main()
