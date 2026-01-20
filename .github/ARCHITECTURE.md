# Architecture: Triggering Workflows Across All Repositories

## High-Level Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         User Actions                             │
└─────────────────────────────────────────────────────────────────┘
                                 │
                    ┌────────────┴────────────┐
                    │                         │
                    ▼                         ▼
         ┌──────────────────┐     ┌─────────────────────┐
         │  GitHub Actions  │     │  Command Line       │
         │  Web Interface   │     │  Script             │
         └──────────────────┘     └─────────────────────┘
                    │                         │
                    │                         │
                    ▼                         ▼
         ┌──────────────────────────────────────────────┐
         │   trigger_workflow_all_repos.py              │
         │   - Authenticates with GH_PAT                │
         │   - Calls GitHub Organization API            │
         │   - Iterates through all repositories        │
         │   - Triggers workflows                       │
         └──────────────────────────────────────────────┘
                                 │
                                 ▼
         ┌──────────────────────────────────────────────┐
         │          GitHub REST API                     │
         │   - /orgs/{org}/repos (list all)            │
         │   - /repos/{repo}/actions/workflows (check)  │
         │   - /repos/{repo}/actions/.../dispatches     │
         └──────────────────────────────────────────────┘
                                 │
                    ┌────────────┴────────────┐
                    │                         │
                    ▼                         ▼
         ┌──────────────────┐     ┌─────────────────────┐
         │  Public Repos    │     │  Private Repos      │
         │  (3 repos)       │     │  (~16 repos)        │
         │  - PhoenixBoot   │     │  - Hidden without   │
         │  - pf-runner     │     │    proper token     │
         │  - .github       │     │    scopes           │
         └──────────────────┘     └─────────────────────┘
                    │                         │
                    └────────────┬────────────┘
                                 ▼
                    ┌────────────────────────┐
                    │  Workflow Triggered    │
                    │  in Each Repository    │
                    └────────────────────────┘
```

## Component Details

### 1. User Interfaces

#### A. GitHub Actions Web Interface
```yaml
workflows/trigger-all-repos.yml
├── Triggered by: Manual workflow_dispatch
├── Inputs: workflow_file, ref, include_archived, check_only
├── Environment: Ubuntu runner
├── Dependencies: Python 3.11, requests library
└── Output: Workflow summary with results
```

#### B. Command Line Interface
```bash
trigger_workflow_all_repos.py
├── Arguments: org, workflow, --ref, --token, --input
├── Options: --check-only, --include-archived, --delay
├── Input: GITHUB_TOKEN or GH_TOKEN environment variable
└── Output: Console output with progress and summary
```

### 2. Core Script Architecture

```python
trigger_workflow_all_repos.py
│
├── get_all_repos(org, token)
│   ├── Calls: GET /orgs/{org}/repos
│   ├── Pagination: Handles multiple pages (100 per page)
│   ├── Fallback: Tries user endpoint if org fails
│   └── Returns: List of all repository objects
│
├── workflow_exists(owner, repo, workflow, token)
│   ├── Calls: GET /repos/{owner}/{repo}/actions/workflows/{workflow}
│   ├── Returns: True if workflow exists, False otherwise
│   └── Purpose: Prevents errors when triggering non-existent workflows
│
├── trigger_workflow(owner, repo, workflow, ref, inputs, token)
│   ├── Calls: POST /repos/{owner}/{repo}/actions/workflows/{workflow}/dispatches
│   ├── Payload: {"ref": branch, "inputs": {...}}
│   ├── Returns: (success: bool, message: str)
│   └── Handles: 204 success, 404 not found, other errors
│
└── main()
    ├── Parse command line arguments
    ├── Validate token availability
    ├── Get all repositories
    ├── For each repository:
    │   ├── Check if workflow exists
    │   ├── Trigger workflow (if not check-only)
    │   └── Apply rate limiting delay
    └── Print summary statistics
```

## Data Flow

### Sequence Diagram

```
User              GitHub UI        Workflow         Script          GitHub API       Repositories
  │                   │               │               │                 │                │
  │ Run workflow      │               │               │                 │                │
  ├──────────────────>│               │               │                 │                │
  │                   │ Trigger job   │               │                 │                │
  │                   ├──────────────>│               │                 │                │
  │                   │               │ Execute       │                 │                │
  │                   │               ├──────────────>│                 │                │
  │                   │               │               │ List repos      │                │
  │                   │               │               ├────────────────>│                │
  │                   │               │               │ [All 19 repos]  │                │
  │                   │               │               │<────────────────┤                │
  │                   │               │               │                 │                │
  │                   │               │               │ For each repo:  │                │
  │                   │               │               │ Check workflow  │                │
  │                   │               │               ├────────────────>│                │
  │                   │               │               │ [exists/not]    │                │
  │                   │               │               │<────────────────┤                │
  │                   │               │               │                 │                │
  │                   │               │               │ Trigger workflow│                │
  │                   │               │               ├────────────────>│                │
  │                   │               │               │                 │ Start workflow │
  │                   │               │               │                 ├───────────────>│
  │                   │               │               │ [204 success]   │                │
  │                   │               │               │<────────────────┤                │
  │                   │               │               │                 │                │
  │                   │               │               │ (repeat for all)│                │
  │                   │               │               │                 │                │
  │                   │               │ Summary       │                 │                │
  │                   │               │<──────────────┤                 │                │
  │                   │ Complete      │               │                 │                │
  │<──────────────────┼───────────────┤               │                 │                │
  │                   │               │               │                 │                │
```

## Authentication Flow

```
┌─────────────────────────────────────────────────────────────┐
│  Step 1: User Creates Personal Access Token (PAT)          │
│  ┌────────────────────────────────────────────────────┐   │
│  │  Scopes:                                            │   │
│  │  ✓ repo       - Access private repositories        │   │
│  │  ✓ workflow   - Trigger workflows                  │   │
│  │  ✓ read:org   - List organization repositories     │   │
│  └────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  Step 2: Token Stored as Repository Secret                 │
│  ┌────────────────────────────────────────────────────┐   │
│  │  Secret Name: GH_PAT                                │   │
│  │  Accessible by: GitHub Actions workflows            │   │
│  │  Used for: GITHUB_TOKEN environment variable        │   │
│  └────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  Step 3: Script Uses Token for API Calls                   │
│  ┌────────────────────────────────────────────────────┐   │
│  │  Authorization: token {GH_PAT}                      │   │
│  │  Sent with: Every API request                       │   │
│  │  Grants: Access to all org repositories             │   │
│  └────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  Step 4: GitHub API Validates and Returns Data             │
│  ┌────────────────────────────────────────────────────┐   │
│  │  Validates: Token signature and scopes              │   │
│  │  Returns: All 19 repositories (public + private)    │   │
│  │  Allows: Workflow dispatch on all repos             │   │
│  └────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

## Error Handling Strategy

```
┌─────────────────────┐
│  API Call           │
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐     Yes    ┌──────────────────┐
│ Success (200/204)?  ├───────────>│ Continue         │
└──────┬──────────────┘            └──────────────────┘
       │ No
       ▼
┌─────────────────────┐     Yes    ┌──────────────────┐
│ Not Found (404)?    ├───────────>│ Skip repo        │
└──────┬──────────────┘            │ Log "not found"  │
       │ No                         └──────────────────┘
       ▼
┌─────────────────────┐     Yes    ┌──────────────────┐
│ Unauthorized (401)? ├───────────>│ Print error      │
└──────┬──────────────┘            │ Exit with code 1 │
       │ No                         └──────────────────┘
       ▼
┌─────────────────────┐     Yes    ┌──────────────────┐
│ Rate Limited (429)? ├───────────>│ Wait & retry     │
└──────┬──────────────┘            │ (via delay)      │
       │ No                         └──────────────────┘
       ▼
┌─────────────────────┐
│ Log error           │
│ Continue to next    │
└─────────────────────┘
```

## Rate Limiting

```python
# Default: 1 second between requests
# GitHub Actions: 1.5 seconds
# User configurable via --delay flag

for repo in repos:
    # Make API call
    trigger_workflow(...)
    
    # Wait before next request
    time.sleep(delay)  # Prevents rate limit errors
```

**GitHub Rate Limits:**
- Authenticated: 5,000 requests/hour
- For 19 repos: ~60 requests max (list + check + trigger)
- With 1.5s delay: ~30 seconds total
- Well within rate limits

## Security Architecture

```
┌─────────────────────────────────────────────────────────┐
│  Defense Layers                                          │
├─────────────────────────────────────────────────────────┤
│  1. Token Storage                                        │
│     • Stored in GitHub Secrets (encrypted at rest)      │
│     • Never exposed in logs or outputs                  │
│     • Accessed only by authorized workflows             │
├─────────────────────────────────────────────────────────┤
│  2. Token Scopes (Principle of Least Privilege)         │
│     • Only required scopes granted                      │
│     • No admin or destructive permissions               │
│     • Read-only where possible (read:org)               │
├─────────────────────────────────────────────────────────┤
│  3. Input Validation                                     │
│     • All inputs validated before use                   │
│     • Error on invalid formats                          │
│     • No shell injection possible                       │
├─────────────────────────────────────────────────────────┤
│  4. API Communication                                    │
│     • HTTPS only (enforced by GitHub)                   │
│     • Token in Authorization header                     │
│     • No credentials in URL parameters                  │
├─────────────────────────────────────────────────────────┤
│  5. Rate Limiting                                        │
│     • Prevents abuse                                    │
│     • Built-in delays                                   │
│     • Respects GitHub API limits                        │
├─────────────────────────────────────────────────────────┤
│  6. Audit Trail                                          │
│     • All workflow runs logged                          │
│     • GitHub Actions audit available                    │
│     • Timestamps and results recorded                   │
└─────────────────────────────────────────────────────────┘
```

## Scalability

**Current: 19 repositories**
- Execution time: ~30 seconds
- API calls: ~60 (list + check + trigger per repo)
- Rate limit usage: <1% of hourly quota

**Scaling to 100 repositories**
- Execution time: ~2.5 minutes
- API calls: ~300
- Rate limit usage: ~6% of hourly quota
- Still well within limits

**Scaling to 1000 repositories**
- Execution time: ~25 minutes
- API calls: ~3000
- Rate limit usage: ~60% of hourly quota
- May need increased delays or batching

## Future Enhancements

Potential improvements for future versions:

1. **Parallel Execution**
   - Use threading for concurrent triggers
   - Reduce total execution time
   - Maintain rate limit compliance

2. **Progress Bar**
   - Visual progress indicator
   - ETA for completion
   - Better user experience

3. **Result Filtering**
   - Filter repos by language, size, or topic
   - Target specific subsets
   - More flexible selection

4. **Retry Logic**
   - Automatic retry on transient failures
   - Exponential backoff
   - Better reliability

5. **Webhook Integration**
   - Trigger on external events
   - Repository webhook listeners
   - Event-driven automation

---

**Version**: 1.0.0  
**Last Updated**: 2025-11-14  
**Status**: Production Ready
