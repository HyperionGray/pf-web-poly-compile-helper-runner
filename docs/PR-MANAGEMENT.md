# PR Management System Documentation

## Overview

The PR Management System provides AI-assisted pull request discovery, review, and merging capabilities for GitHub and GitLab repositories. It integrates seamlessly with the pf task runner and supports multiple AI providers for automated code review.

## Features

- 🔍 **Automated PR Discovery**: Discover pull requests across multiple repositories and platforms
- 🤖 **AI-Powered Code Review**: Automated code review using OpenAI GPT-4, Anthropic Claude, and other providers
- 🔀 **Safe Automated Merging**: Batch merge approved PRs with comprehensive safety checks
- 📊 **Interactive Dashboard**: Real-time status dashboard with metrics and quick actions
- ⚠️ **Conflict Detection**: Identify and resolve merge conflicts with AI assistance
- 📈 **Analytics & Reporting**: Generate detailed reports on PR activity and trends

## Quick Start

### 1. Installation

Install the required CLI tools:

```bash
pf install-pr-tools
```

This installs:
- GitHub CLI (`gh`)
- GitLab CLI (`glab`)
- JSON processor (`jq`)

### 2. Authentication

Authenticate with your Git platforms:

```bash
# GitHub
gh auth login

# GitLab
glab auth login
```

### 3. Configure AI Providers

Set up your AI provider credentials:

```bash
# OpenAI
export OPENAI_API_KEY="your-api-key"

# Anthropic Claude
export ANTHROPIC_API_KEY="your-api-key"

# Configure providers
pf pr-ai-config provider=openai api_key=$OPENAI_API_KEY model=gpt-4
```

### 4. Discover Pull Requests

```bash
# Discover PRs in current repository
pf pr-discover

# Discover PRs in specific repository
pf pr-discover repo=owner/repository

# Discover across multiple platforms
pf pr-discover platform=auto
```

### 5. Review and Merge

```bash
# View discovered PRs
pf pr-list

# AI review all PRs
pf pr-review-all-ai

# Merge approved PRs
pf pr-merge-all

# Interactive dashboard
pf pr-status-dashboard
```

## Detailed Usage

### PR Discovery

The discovery system can find PRs from:
- Current git repository (auto-detected)
- Specific repositories
- Multiple configured repositories

```bash
# Basic discovery
pf pr-discover

# Specific repository
pf pr-discover repo=myorg/myproject

# Specific platform
pf pr-discover platform=github

# Multiple repositories (configure in ~/.config/pf/pr-config.json)
pf pr-discover
```

### AI Code Review

The AI review system supports multiple providers and models:

```bash
# Review specific PR
pf pr-review-ai pr_id=123

# Use different AI provider
pf pr-review-ai pr_id=123 provider=anthropic model=claude-3

# Batch review all PRs
pf pr-review-all-ai provider=openai model=gpt-4 max_concurrent=3
```

#### Review Criteria

The AI reviewer evaluates:
1. **Security**: Vulnerabilities, input validation, authentication issues
2. **Performance**: Bottlenecks, inefficient algorithms, resource usage
3. **Maintainability**: Code readability, documentation, structure
4. **Testing**: Test coverage, quality, edge cases
5. **Best Practices**: Language-specific standards and conventions

#### Review Output

Reviews are saved in structured JSON format:

```json
{
  "overall_score": 8,
  "recommendation": "APPROVE",
  "summary": "Well-structured code with good test coverage",
  "issues": [
    {
      "severity": "MEDIUM",
      "category": "performance",
      "description": "Consider using more efficient algorithm",
      "suggestion": "Replace O(n²) loop with O(n log n) sort",
      "line_numbers": [45, 46, 47]
    }
  ],
  "positive_aspects": [
    "Comprehensive error handling",
    "Good documentation"
  ],
  "suggestions": [
    "Add integration tests",
    "Consider adding performance benchmarks"
  ]
}
```

### Automated Merging

The merge system includes comprehensive safety checks:

```bash
# Merge all approved PRs
pf pr-merge-all

# Use specific merge strategy
pf pr-merge-all strategy=squash

# Require both human and AI approval
pf pr-merge-all require_reviews=true require_ai_approval=true

# Dry run (preview without merging)
pf pr-merge-all dry_run=true
```

#### Merge Strategies

- **squash**: Squash all commits into one (default)
- **merge**: Create merge commit
- **rebase**: Rebase and merge

#### Safety Checks

Before merging, the system verifies:
- ✅ PR is mergeable
- ✅ No merge conflicts
- ✅ Status checks pass
- ✅ Has required approvals
- ✅ Up-to-date with target branch

### Dashboard and Monitoring

The interactive dashboard provides real-time insights:

```bash
# Static dashboard
pf pr-status-dashboard

# Auto-refreshing dashboard (every 30 seconds)
pf pr-status-dashboard refresh_interval=30
```

Dashboard sections:
- **Overview Metrics**: Total PRs, ready to merge, needs attention
- **Platform Breakdown**: GitHub vs GitLab distribution
- **Status Breakdown**: Open, merged, closed PRs
- **Review Status**: Approved, pending, changes requested
- **Top Priority PRs**: Ready to merge, needs attention, pending review
- **Quick Actions**: Suggested next steps
- **Recent Activity**: Latest PR updates

### Conflict Management

Detect and resolve merge conflicts:

```bash
# Detect conflicts across all PRs
pf pr-conflict-detect

# AI-assisted conflict resolution
pf pr-conflict-resolve pr_id=123

# Auto-apply AI suggestions
pf pr-conflict-resolve pr_id=123 auto_apply=true
```

### Analytics and Reporting

Generate comprehensive reports:

```bash
# Generate analytics report
pf pr-analytics period=30d format=html output=pr-report.html

# JSON format for CI/CD integration
pf pr-analytics period=7d format=json output=weekly-report.json

# Console output
pf pr-analytics period=1d format=console
```

## Configuration

### Main Configuration

Create `~/.config/pf/pr-config.json`:

```json
{
  "repositories": [
    {"repo": "myorg/project1", "platform": "github"},
    {"repo": "myorg/project2", "platform": "gitlab"}
  ],
  "platforms": {
    "github": {"enabled": true},
    "gitlab": {"enabled": true}
  },
  "filters": {
    "states": ["open"],
    "labels": ["ready-for-review"],
    "authors": []
  },
  "merging": {
    "defaultStrategy": "squash",
    "requireReviews": true,
    "requireAiApproval": true,
    "autoDeleteBranch": true
  }
}
```

### AI Provider Configuration

Create `~/.config/pf/ai-providers.json`:

```json
{
  "providers": {
    "openai": {
      "apiKey": "sk-...",
      "model": "gpt-4",
      "enabled": true,
      "maxTokens": 2000,
      "temperature": 0.1
    },
    "anthropic": {
      "apiKey": "sk-ant-...",
      "model": "claude-3-sonnet-20240229",
      "enabled": true,
      "maxTokens": 2000
    }
  },
  "reviewCriteria": {
    "security": true,
    "performance": true,
    "maintainability": true,
    "testCoverage": true,
    "documentation": true
  },
  "batchSettings": {
    "maxConcurrent": 3,
    "delayBetweenBatches": 5000,
    "retryAttempts": 2
  }
}
```

## Advanced Features

### Webhook Integration

Set up webhooks for automated processing:

```bash
# Setup webhook endpoint
pf pr-setup-webhooks endpoint_url=https://your-server.com/webhook secret=your-secret

# Process webhook events automatically
pf pr-webhook-handler
```

### Batch Processing

Process multiple PRs efficiently:

```bash
# Batch process with custom filters
pf pr-batch-process filter=ready max_concurrent=5

# Process only specific repositories
pf pr-batch-process filter=repo:myorg/project1

# Dry run batch processing
pf pr-batch-process dry_run=true
```

### Custom Filters

Filter PRs using various criteria:

```bash
# List mergeable PRs
pf pr-list filter=mergeable

# List PRs needing review
pf pr-list filter=needs-review

# List approved PRs
pf pr-list filter=approved

# List PRs with conflicts
pf pr-list filter=conflicts

# List AI-reviewed PRs
pf pr-list filter=ai-reviewed

# List ready-to-merge PRs
pf pr-list filter=ready-to-merge
```

## Troubleshooting

### Common Issues

1. **Authentication Errors**
   ```bash
   # Re-authenticate
   gh auth login
   glab auth login
   
   # Check authentication status
   gh auth status
   glab auth status
   ```

2. **API Rate Limits**
   ```bash
   # Check rate limit status
   gh api rate_limit
   
   # Use lower concurrency
   pf pr-review-all-ai max_concurrent=1
   ```

3. **Large Diffs**
   - Large PRs are automatically truncated for AI review
   - Consider splitting large PRs into smaller ones
   - Use `pf pr-conflict-detect` to identify problematic PRs

4. **Missing Dependencies**
   ```bash
   # Reinstall tools
   pf install-pr-tools
   
   # Check tool availability
   which gh glab jq
   ```

### Debug Mode

Enable verbose logging:

```bash
export PF_DEBUG=1
pf pr-discover
```

### Data Locations

- PR data: `~/.config/pf/discovered-prs.json`
- AI reviews: `~/.config/pf/reviews/`
- Merge results: `~/.config/pf/merge-results/`
- Configuration: `~/.config/pf/pr-config.json`
- AI config: `~/.config/pf/ai-providers.json`

## Integration with CI/CD

### GitHub Actions

```yaml
name: PR Management
on:
  schedule:
    - cron: '0 */6 * * *'  # Every 6 hours
  workflow_dispatch:

jobs:
  pr-management:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Setup pf
        run: |
          ./install.sh base
          pf install-pr-tools
      - name: Configure AI
        env:
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
        run: |
          pf pr-ai-config provider=openai api_key=$OPENAI_API_KEY
      - name: Process PRs
        run: |
          pf pr-discover
          pf pr-review-all-ai
          pf pr-merge-all dry_run=true  # Remove dry_run for actual merging
```

### GitLab CI

```yaml
pr-management:
  stage: maintenance
  script:
    - ./install.sh base
    - pf install-pr-tools
    - pf pr-ai-config provider=openai api_key=$OPENAI_API_KEY
    - pf pr-discover
    - pf pr-review-all-ai
    - pf pr-analytics format=json output=pr-report.json
  artifacts:
    reports:
      junit: pr-report.json
  only:
    - schedules
```

## Best Practices

1. **Regular Discovery**: Run `pf pr-discover` regularly to keep data fresh
2. **AI Review First**: Always run AI reviews before merging
3. **Conflict Resolution**: Address conflicts promptly with `pf pr-conflict-detect`
4. **Batch Processing**: Use batch operations for efficiency
5. **Monitor Dashboard**: Use `pf pr-status-dashboard` for oversight
6. **Backup Configuration**: Keep your config files in version control
7. **Rate Limit Awareness**: Respect API rate limits with appropriate concurrency
8. **Security**: Store API keys securely, never in code

## API Reference

### Command Line Interface

All PR management commands follow the pf task runner pattern:

```bash
pf <command> [param=value] [param2=value2]
```

### Parameters

Common parameters across commands:
- `repo=owner/name`: Target repository
- `platform=github|gitlab|auto`: Git platform
- `provider=openai|anthropic`: AI provider
- `model=gpt-4|claude-3`: AI model
- `dry_run=true|false`: Preview mode
- `max_concurrent=N`: Concurrency limit

### Exit Codes

- `0`: Success
- `1`: General error
- `2`: Authentication error
- `3`: Configuration error
- `4`: API error
- `5`: Network error

## Contributing

To contribute to the PR Management system:

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Update documentation
5. Submit a pull request

The system will automatically review your PR using AI! 🤖

## License

This PR Management system is part of the pf task runner project and follows the same license terms.