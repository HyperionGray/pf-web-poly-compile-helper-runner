#!/usr/bin/env python3
"""
Spread a secret to multiple repositories.

Usage:
  # Set secret via env var and spread to ALL repos in default accounts
  export COPILOT_SECRET_VALUE="my-super-secret-key"
  python spread_secret.py

  # Spread multiple secrets (repeat --secret)
  export OPENAI_API_KEY="..."
  export GEMINI_API_KEY="..."
  export ANTHROPIC_API_KEY="..."
  python spread_secret.py --target ALL \
    --secret OPENAI_API_KEY=OPENAI_API_KEY \
    --secret GEMINI_API_KEY=GEMINI_API_KEY \
    --secret ANTHROPIC_API_KEY=ANTHROPIC_API_KEY

  # Target specific repo
  python spread_secret.py --target "P4X-ng/some-repo"

  # Target wildcard
  python spread_secret.py --target "P4X-ng/*"

  # Specify secret name and env var
  python spread_secret.py --secret-name MY_API_KEY --env-var API_KEY_VAL

Requirements:
  pip install requests pynacl
"""

import os
import sys
import argparse
import base64
import requests
from typing import List, Dict, Any, Optional

try:
    from nacl import encoding, public
except ImportError:
    print("Error: 'pynacl' library is required for secret encryption.")
    print("Run: pip install pynacl")
    sys.exit(1)

DEFAULT_ACCOUNTS = ['P4X-ng', 'HyperionGray', 'TeamHG-Memex', 'hyp3ri0n-ng']


def get_all_repos(owner: str, token: str, include_archived: bool = False) -> List[Dict[str, Any]]:
    """Fetch all repositories for an owner (org or user), including private ones."""
    headers = {
        'Authorization': f'token {token}',
        'Accept': 'application/vnd.github+json',
        'X-GitHub-Api-Version': '2022-11-28'
    }

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

        response = requests.get(url, headers=headers, params=params)

        if response.status_code == 404:
            # Try as user account instead
            url = f'https://api.github.com/users/{owner}/repos'
            response = requests.get(url, headers=headers, params=params)

        if response.status_code != 200:
            print(f"Error fetching repositories: {response.status_code}")
            try:
                print(f"Response: {response.text}")
            except:
                pass
            break

        batch = response.json()
        if not batch:
            break

        repos.extend(batch)
        page += 1

        if len(batch) < per_page:
            break

    if not include_archived:
        repos = [r for r in repos if not r.get('archived', False)]

    return repos


def get_repo_public_key(owner: str, repo: str, token: str) -> Optional[Dict[str, str]]:
    """Get the public key for a repository."""
    url = f"https://api.github.com/repos/{owner}/{repo}/actions/secrets/public-key"
    headers = {
        'Authorization': f'token {token}',
        'Accept': 'application/vnd.github+json',
        'X-GitHub-Api-Version': '2022-11-28'
    }

    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"   Warning: Could not get public key for {owner}/{repo}: {response.status_code}")
        return None


def encrypt_secret(public_key: str, secret_value: str) -> str:
    """Encrypt a secret using the repository's public key."""
    public_key_bytes = base64.b64decode(public_key)
    sealed_box = public.SealedBox(public.PublicKey(public_key_bytes))
    encrypted = sealed_box.encrypt(secret_value.encode("utf-8"))
    return base64.b64encode(encrypted).decode("utf-8")


def set_secret(owner: str, repo: str, secret_name: str, encrypted_value: str, key_id: str, token: str) -> bool:
    """Create or update a repository secret."""
    url = f"https://api.github.com/repos/{owner}/{repo}/actions/secrets/{secret_name}"
    headers = {
        'Authorization': f'token {token}',
        'Accept': 'application/vnd.github+json',
        'X-GitHub-Api-Version': '2022-11-28'
    }

    data = {
        'encrypted_value': encrypted_value,
        'key_id': key_id
    }

    response = requests.put(url, headers=headers, json=data)

    if response.status_code in [201, 204]:
        return True
    else:
        print(f"   Failed to set secret for {owner}/{repo}: {response.status_code}")
        print(f"      {response.text}")
        return False


def main():
    parser = argparse.ArgumentParser(description='Spread a GitHub Action secret across repositories')
    parser.add_argument('--target', default='ALL', help='Target repo(s): "Owner/Repo", "Owner/*", or "ALL"')
    parser.add_argument('--secret', action='append',
                        help='Repeatable: SECRET_NAME=ENV_VAR (e.g., OPENAI_API_KEY=OPENAI_API_KEY)')
    parser.add_argument('--secret-name', default='COPILOT_SECRET', help='Name of the secret to create/update (single-secret mode)')
    parser.add_argument('--env-var', default='COPILOT_SECRET_VALUE', help='Env var containing the secret value (single-secret mode)')
    parser.add_argument('--token', help='GitHub Token')
    parser.add_argument('--owners', default='', help='Comma-separated owners to scan when target is ALL (overrides defaults)')
    parser.add_argument('--include-archived', action='store_true', help='Include archived repositories')
    parser.add_argument('--all-accounts', action='store_true',
                        help='Scan default owners (same as target=ALL with no --owners override)')
    parser.add_argument('--dry-run', action='store_true', help='Show what would change without setting secrets')

    args = parser.parse_args()

    # 1. Get Token
    token = args.token or os.environ.get('GITHUB_TOKEN')
    if not token:
        print("Error: GitHub token required (GITHUB_TOKEN env var or --token)")
        sys.exit(1)

    # 2. Determine secrets to set
    secrets_to_set = []
    if args.secret:
        for spec in args.secret:
            if '=' not in spec:
                print(f"Error: Invalid --secret '{spec}'. Expected SECRET_NAME=ENV_VAR.")
                sys.exit(2)
            secret_name, env_var = spec.split('=', 1)
            secret_name = secret_name.strip()
            env_var = env_var.strip()
            if not secret_name or not env_var:
                print(f"Error: Invalid --secret '{spec}'. Expected SECRET_NAME=ENV_VAR.")
                sys.exit(2)
            secrets_to_set.append((secret_name, env_var))
    else:
        secrets_to_set.append((args.secret_name, args.env_var))

    for secret_name, env_var in secrets_to_set:
        secret_value = os.environ.get(env_var)
        if not secret_value:
            print(f"Error: Environment variable '{env_var}' is not set for secret '{secret_name}'.")
            print(f"Set it first: export {env_var}=\"your-value\"")
            sys.exit(1)

    # 3. Determine Targets
    if args.owners.strip():
        accounts = [o.strip() for o in args.owners.split(',') if o.strip()]
    else:
        accounts = DEFAULT_ACCOUNTS

    all_repos = []

    if args.target in ['ALL', '*', 'all']:
        print(f"Fetching repositories for owners: {', '.join(accounts)}")
        for account in accounts:
            print(f"  Fetching {account}...")
            all_repos.extend(get_all_repos(account, token, include_archived=args.include_archived))

    elif args.target.endswith('/*'):
        owner = args.target.split('/')[0]
        print(f"Fetching repositories for {owner}...")
        all_repos = get_all_repos(owner, token, include_archived=args.include_archived)

    elif '/' in args.target:
        owner, name = args.target.split('/')
        all_repos = [{'name': name, 'owner': {'login': owner}}]
    else:
        # Just a repo name? Assume current user logic or search
        # Ideally user provides Owner/Repo
        print("Error: Target must be 'ALL', 'Owner/*', or 'Owner/Repo'")
        sys.exit(1)

    print(f"Found {len(all_repos)} potential repositories.")

    # 4. Process Repos
    total_ok = 0
    total_failed = 0
    total_skipped = 0

    for repo in all_repos:
        owner = repo['owner']['login']
        name = repo['name']
        full_name = f"{owner}/{name}"

        print(f"Processing {full_name}...")

        # Get public key
        key_data = get_repo_public_key(owner, name, token)
        if not key_data:
            total_failed += 1
            continue

        key_id = key_data['key_id']
        pk_value = key_data['key']

        if args.dry_run:
            for secret_name, env_var in secrets_to_set:
                print(f"  Would set secret '{secret_name}' from env var '{env_var}'")
            total_skipped += 1
            continue

        for secret_name, env_var in secrets_to_set:
            secret_value = os.environ.get(env_var)
            if not secret_value:
                print(f"  Missing env var '{env_var}' for secret '{secret_name}'; skipping repo.")
                total_failed += 1
                break

            # Encrypt
            try:
                encrypted_value = encrypt_secret(pk_value, secret_value)
            except Exception as e:
                print(f"  Encryption failed for '{secret_name}': {e}")
                total_failed += 1
                break

            # Set Secret
            if set_secret(owner, name, secret_name, encrypted_value, key_id, token):
                print(f"  Updated secret '{secret_name}'")
                total_ok += 1
            else:
                total_failed += 1

    print("\n" + "=" * 40)
    print("Finished")
    print(f"  Updated secrets: {total_ok}")
    print(f"  Failed updates:  {total_failed}")
    print(f"  Dry-run repos:   {total_skipped}")

if __name__ == '__main__':
    main()
