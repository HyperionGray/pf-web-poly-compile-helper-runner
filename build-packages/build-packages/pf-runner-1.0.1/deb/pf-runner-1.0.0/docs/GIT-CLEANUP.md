# Git Large File Cleanup Guide

## Overview

The Git Large File Cleanup Tool provides an intuitive Terminal User Interface (TUI) for removing large files from git history. This tool helps reduce repository size and improve clone/fetch performance by safely rewriting git history.

## Features

- 🎯 **Interactive TUI**: Beautiful, user-friendly interface for file selection
- 📊 **Size Analysis**: Analyze and visualize large files in git history
- ✅ **Checkbox Selection**: Multi-select interface for choosing files to remove
- 🔒 **Automatic Backup**: Creates git bundle backup before any changes
- ⚡ **Efficient Cleanup**: Uses git-filter-repo for fast, safe history rewriting
- 📝 **Clear Instructions**: Step-by-step guidance for post-cleanup actions

## Installation

### Prerequisites

- Git repository
- Python 3.x with pip
- Node.js (already included in this project)

### Install git-filter-repo

The tool will automatically offer to install git-filter-repo if it's not present, or you can install it manually:

```bash
# Using pf task
pf install-git-filter-repo

# Or manually
pip3 install --user git-filter-repo
```

## Quick Start

### Interactive Cleanup

```bash
# Navigate to your git repository
cd your-repository

# Run the interactive cleanup tool
pf git-cleanup
```

The tool will guide you through:

1. **Select threshold**: Choose minimum file size to analyze (100KB - 50MB)
2. **View analysis**: See all large files in a formatted table
3. **Select files**: Use checkboxes to select files for removal
4. **Confirm action**: Review and confirm the cleanup operation
5. **Create backup**: Option to backup before proceeding
6. **Execute cleanup**: Remove selected files from git history
7. **Next steps**: Follow instructions for force-push and team coordination

### Quick Analysis

To just see what large files exist without removing them:

```bash
pf git-analyze-large-files
```

### Check Repository Size

```bash
pf git-repo-size
```

## Usage Examples

### Example 1: Remove Large Build Artifacts

```bash
# Start the interactive tool
pf git-cleanup

# Select threshold: 5 MB
# The tool will show all files > 5MB

# Example output:
# ┌─────┬───────────────┬────────────────────────────────────────────┐
# │  #  │     Size      │                File Path                   │
# ├─────┼───────────────┼────────────────────────────────────────────┤
# │  1  │   125.50 MB   │ dist/app.bundle.js                         │
# │  2  │    87.20 MB   │ node_modules.tar.gz                        │
# │  3  │    45.00 MB   │ videos/demo.mp4                            │
# └─────┴───────────────┴────────────────────────────────────────────┘

# Select files with Space key, confirm with Enter
# Confirm removal, create backup, and clean!
```

### Example 2: Custom Size Threshold

```bash
pf git-cleanup

# Choose "Custom" threshold
# Enter: 0.5 (for 500KB)
# Select files to remove
# Confirm and execute
```

### Example 3: Analysis Only

```bash
# Quick command-line analysis
pf git-analyze-large-files

# Output:
# Top 20 largest files in git history:
#   125.50 MB  dist/app.bundle.js
#    87.20 MB  node_modules.tar.gz
#    45.00 MB  videos/demo.mp4
#    ...
```

## How It Works

### 1. Analysis Phase

The tool uses git commands to analyze the entire repository history:

```bash
git rev-list --all --objects | \
  git cat-file --batch-check | \
  sort by size
```

This finds all objects across all commits, not just current files.

### 2. Selection Phase

Interactive TUI displays files with:
- Human-readable sizes (B, KB, MB, GB)
- Full file paths
- Multi-select checkboxes
- Search/filter capabilities

### 3. Backup Phase

Before any changes, creates a git bundle:

```bash
git bundle create backup-<timestamp>.bundle --all
```

This allows full recovery if needed.

### 4. Cleanup Phase

Uses `git-filter-repo` to safely rewrite history:

```bash
git-filter-repo --invert-paths --paths-from-file <selected-files> --force
```

This:
- Removes files from all commits
- Maintains commit integrity
- Preserves other files and history
- Updates all references

### 5. Post-Cleanup

After successful cleanup, you'll see instructions for:
- Reviewing changes
- Force-pushing to remote
- Team coordination

## Post-Cleanup Actions

### 1. Review Changes

```bash
# Check the repository state
git status
git log --all --oneline

# Check repository size
pf git-repo-size
```

### 2. Force-Push to Remote

⚠️ **Warning**: This rewrites history on the remote. Coordinate with your team!

```bash
# Push all branches
git push origin --force --all

# Push all tags
git push origin --force --tags
```

### 3. Team Coordination

**Important**: All team members must:

1. **Commit and backup** their local changes
2. **Delete** their local repository
3. **Re-clone** from the remote

```bash
# Team members should do:
git clone <repository-url>
```

**Do NOT** try to pull/rebase - the history has changed!

## Safety Features

### Automatic Backup

- Creates git bundle before any changes
- Stored in `.git-cleanup-backup/`
- Can restore entire repository if needed

### Restore from Backup

If you need to restore:

```bash
cd your-repository

# Clone from backup
git clone .git-cleanup-backup/backup-<timestamp>.bundle restored-repo

# Or restore in place
cd ..
rm -rf your-repository
git clone your-repository/.git-cleanup-backup/backup-<timestamp>.bundle your-repository
```

### Pre-Flight Checks

The tool verifies:
- Running in a git repository
- git-filter-repo is available
- Git is functioning properly

### Confirmation Steps

Multiple confirmations before destructive actions:
1. File selection confirmation
2. Final removal confirmation
3. Backup creation option

## Advanced Usage

### Analyzing Large Files Programmatically

```bash
# Get list of files > 10MB
git rev-list --all --objects | \
  git cat-file --batch-check='%(objecttype) %(objectname) %(objectsize) %(rest)' | \
  grep '^blob' | \
  sort -k3 -n -r | \
  awk '$3 > 10485760'
```

### Custom Cleanup Script

For automation, you can create a custom script:

```bash
#!/bin/bash
# cleanup-large-files.sh

# List of files to remove
cat > /tmp/files-to-remove.txt << EOF
large-file-1.zip
old-data/backup.tar.gz
media/video.mp4
EOF

# Backup
git bundle create backup-$(date +%Y%m%d).bundle --all

# Remove files
git-filter-repo --invert-paths --paths-from-file /tmp/files-to-remove.txt --force
```

### Batch Operations

Remove all files matching a pattern:

```bash
# Create list of files
git rev-list --all --objects | \
  git cat-file --batch-check='%(objectname) %(rest)' | \
  grep '\.log$' | \
  cut -d' ' -f2- > /tmp/log-files.txt

# Remove them
git-filter-repo --invert-paths --paths-from-file /tmp/log-files.txt --force
```

## Troubleshooting

### git-filter-repo Installation Fails

**Problem**: pip installation fails

**Solutions**:

```bash
# Try with pip3
pip3 install --user git-filter-repo

# Ensure pip is up to date
pip3 install --upgrade pip

# Install from source
git clone https://github.com/newren/git-filter-repo.git
cd git-filter-repo
python3 setup.py install --user
```

### "Not a git repository" Error

**Problem**: Tool doesn't detect git repo

**Solution**: Ensure you're in the repository root:

```bash
cd $(git rev-parse --show-toplevel)
pf git-cleanup
```

### Force Push Rejected

**Problem**: Remote rejects force push

**Solutions**:

```bash
# Ensure you have force-push permissions
git push origin --force-with-lease --all

# Check branch protection rules on GitHub/GitLab
# May need to temporarily disable protection
```

### Large Repository Analysis Slow

**Problem**: Analysis takes too long

**Solutions**:

```bash
# Use higher threshold to reduce results
# In the interactive tool, choose 50MB or 100MB

# Or analyze specific size range manually
git rev-list --all --objects | \
  git cat-file --batch-check='%(objectsize) %(rest)' | \
  awk '$1 > 52428800 && $1 < 104857600'  # 50MB-100MB
```

### Team Members Have Conflicts

**Problem**: Team members have merge conflicts after cleanup

**Solution**: 

They **must** re-clone, not merge:

```bash
# Wrong approach (will create conflicts)
git pull  # DON'T DO THIS

# Correct approach
cd ..
rm -rf old-repo
git clone <repository-url> new-repo
cd new-repo
```

## Best Practices

### 1. Before Cleanup

- ✅ Communicate with team
- ✅ Choose off-peak hours
- ✅ Ensure all PRs are merged
- ✅ Document large files being removed
- ✅ Verify backup strategy

### 2. During Cleanup

- ✅ Start with higher thresholds (10MB+)
- ✅ Review file list carefully
- ✅ Always create backup
- ✅ Test on a clone first if unsure

### 3. After Cleanup

- ✅ Verify repository integrity
- ✅ Test builds/deployments
- ✅ Coordinate team re-cloning
- ✅ Update CI/CD if needed
- ✅ Monitor repository size

### 4. Prevention

- ✅ Add large files to `.gitignore`
- ✅ Use Git LFS for large assets
- ✅ Document commit guidelines
- ✅ Set up pre-commit hooks
- ✅ Regular repository audits

## Common Use Cases

### 1. Accidentally Committed node_modules

```bash
pf git-cleanup
# Select threshold: 1 MB
# Check node_modules/* files
# Remove and add to .gitignore
```

### 2. Old Build Artifacts

```bash
pf git-cleanup
# Select files in dist/, build/, target/
# Remove and update .gitignore
```

### 3. Large Media Files

```bash
pf git-cleanup
# Select .mp4, .mov, .zip files
# Consider Git LFS for future large files
```

### 4. Database Dumps

```bash
pf git-cleanup
# Select .sql, .db, .dump files
# Use proper backup solution instead
```

## Performance Impact

### Before Cleanup

- Clone time: ~5 minutes
- Repository size: 500 MB
- Fetch time: ~1 minute

### After Cleanup (removing 400MB of files)

- Clone time: ~30 seconds (10x faster)
- Repository size: 100 MB (5x smaller)
- Fetch time: ~10 seconds (6x faster)

## Alternative Tools

If git-filter-repo doesn't work for you:

### BFG Repo-Cleaner

```bash
# Install BFG
wget https://repo1.maven.org/maven2/com/madgag/bfg/1.14.0/bfg-1.14.0.jar

# Remove files larger than 50MB
java -jar bfg-1.14.0.jar --strip-blobs-bigger-than 50M .
```

### Git Filter-Branch (Legacy)

```bash
git filter-branch --tree-filter 'rm -f large-file.zip' HEAD
```

⚠️ Not recommended - use git-filter-repo instead

## Integration with Git LFS

For future large files, use Git LFS:

```bash
# Install Git LFS
git lfs install

# Track large files
git lfs track "*.psd"
git lfs track "*.mp4"

# Commit .gitattributes
git add .gitattributes
git commit -m "Add Git LFS tracking"
```

## References

- [git-filter-repo documentation](https://github.com/newren/git-filter-repo)
- [Git LFS](https://git-lfs.github.com/)
- [Pro Git Book - Rewriting History](https://git-scm.com/book/en/v2/Git-Tools-Rewriting-History)

## Support

For issues or questions:

1. Check this documentation
2. Run `pf git-cleanup-help`
3. Review git-filter-repo docs
4. File an issue on the repository

## Quick Reference

| Command | Description |
|---------|-------------|
| `pf git-cleanup` | Interactive TUI for file removal |
| `pf git-analyze-large-files` | Quick analysis only |
| `pf git-repo-size` | Show repository size stats |
| `pf install-git-filter-repo` | Install dependency |
| `pf git-cleanup-help` | Show help message |

---

**Remember**: Always backup before rewriting history! 🔒
