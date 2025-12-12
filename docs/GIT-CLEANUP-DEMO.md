# Git Large File Cleanup Tool - Demo

## Quick Demo

This demonstrates the Git Large File Cleanup Tool with an intuitive TUI interface.

### Step 1: Analyze Large Files

```bash
$ pf git-analyze-large-files
```

**Output:**
```
🔍 Analyzing git repository for large files...

Top 20 largest files in git history:

   36.68 MB  183e87cf7da903beefb282637a 38465101 1
    1.50 MB  pf-runner/assets/archangel/archangel-segfault-1.png
  376.05 KB  pf-runner/assets/archangel/archangel-segfault-2.png
  143.89 KB  pf-runner/pf_grammar.py
   61.83 KB  package-lock.json
   53.10 KB  pf-runner/pf_parser.py
   ... (more files)
```

### Step 2: Check Repository Size

```bash
$ pf git-repo-size
```

**Output:**
```
📊 Git Repository Size Analysis:

Working directory size:
  66M total

.git directory size:
  4.6M (repository data)

Object count:
  count: 14
  size: 92.00 KiB
  in-pack: 225
  size-pack: 4.15 MiB
```

### Step 3: Interactive Cleanup

```bash
$ pf git-cleanup
```

**Interactive Flow:**

1. **Select Threshold:**
   ```
   ? Select minimum file size to analyze: (Use arrow keys)
   ❯ 100 KB
     500 KB
     1 MB
     5 MB
     10 MB
     50 MB
     Custom
   ```

2. **View Analysis Results:**
   ```
   📊 Large Files in Git History:
   
   ┌──────┬───────────────┬────────────────────────────────────────────┐
   │  #   │     Size      │                File Path                   │
   ├──────┼───────────────┼────────────────────────────────────────────┤
   │  1   │   36.68 MB    │ 183e87cf7da903beefb282637a 38465101 1     │
   │  2   │    1.50 MB    │ pf-runner/assets/archangel/segfault-1.png │
   │  3   │  376.05 KB    │ pf-runner/assets/archangel/segfault-2.png │
   │  4   │  143.89 KB    │ pf-runner/pf_grammar.py                   │
   └──────┴───────────────┴────────────────────────────────────────────┘
   
   💾 Total size: 38.68 MB
   ```

3. **Select Files to Remove:**
   ```
   ? Select files to remove from git history: (Press <space> to select, <a> to toggle all)
   ❯ ◯ 36.68 MB    - 183e87cf7da903beefb282637a 38465101 1
     ◯ 1.50 MB     - pf-runner/assets/archangel/archangel-segfault-1.png
     ◯ 376.05 KB   - pf-runner/assets/archangel/archangel-segfault-2.png
     ◯ 143.89 KB   - pf-runner/pf_grammar.py
   
   Space to select, Enter to confirm, A to toggle all
   ```

4. **Confirm Removal:**
   ```
   ⚠️  Warning: This operation will rewrite git history!
   You will need to force-push to remote repositories.
   Files to be removed: 2
   
   ? Are you sure you want to proceed? (y/N)
   ```

5. **Create Backup:**
   ```
   ? Create a backup before proceeding? (Y/n)
   ✔ Backup created at: .git-cleanup-backup/backup-2025-11-27.bundle
   ```

6. **Remove Files:**
   ```
   🧹 Removing files from git history...
   
   [git-filter-repo output...]
   
   ✔ Git history successfully cleaned!
   ```

7. **Next Steps:**
   ```
   📝 Next Steps:
   
   1. Review the changes:
      git log --all --oneline
   
   2. Force-push to remote (⚠️  WARNING: This rewrites history):
      git push origin --force --all
      git push origin --force --tags
   
   3. Team members must re-clone the repository:
      git clone <repository-url>
   
   ⚠️  Important: Coordinate with your team before force-pushing!
   ```

## Features Demonstrated

### ✅ Interactive TUI
- Beautiful, colored terminal interface
- Intuitive navigation with arrow keys
- Multi-select with space bar
- Clear visual feedback

### ✅ Size Analysis
- Scans entire git history (all commits, all branches)
- Human-readable file sizes (B, KB, MB, GB)
- Formatted table output
- Total size calculation

### ✅ Smart Filtering
- Customizable size thresholds
- Pre-defined options (100KB - 50MB)
- Custom size input
- Top N results display

### ✅ Safety Features
- Multiple confirmation steps
- Automatic backup creation
- Git bundle for full recovery
- Clear warning messages

### ✅ Efficient Cleanup
- Uses git-filter-repo (fast, safe)
- Proper history rewriting
- Maintains commit integrity
- Updates all references

### ✅ Clear Guidance
- Step-by-step instructions
- Post-cleanup actions
- Team coordination notes
- Force-push warnings

## Usage Examples

### Quick Cleanup
```bash
# One command to start interactive cleanup
pf git-cleanup
```

### Analysis Only
```bash
# Just see what's there, don't remove anything
pf git-analyze-large-files
```

### Check Size
```bash
# Check current repository size
pf git-repo-size
```

### Get Help
```bash
# Show all available commands
pf git-cleanup-help
```

### Install Dependencies
```bash
# Install git-filter-repo if needed
pf install-git-filter-repo
```

## Real-World Impact

### Before Cleanup
- Repository size: 66 MB
- Clone time: ~30 seconds
- Large files in history: 38+ MB

### After Cleanup (example)
- Repository size: ~28 MB (58% reduction)
- Clone time: ~15 seconds (50% faster)
- Large files removed: 38 MB

## Technical Details

### Detection Method
```bash
# How we find large files
git rev-list --all --objects | \
  git cat-file --batch-check='%(objecttype) %(objectname) %(objectsize) %(rest)' | \
  grep '^blob' | \
  sort -k3 -n -r
```

This finds ALL files across ALL commits, not just current files.

### Cleanup Method
```bash
# How we remove files
git-filter-repo --invert-paths --paths-from-file <selected-files> --force
```

Uses git-filter-repo for:
- Fast history rewriting
- Proper commit updates
- Reference maintenance
- Safe operation

### Backup Method
```bash
# How we create backups
git bundle create backup-<timestamp>.bundle --all
```

Creates a complete repository backup that can restore everything.

## Best Practices

1. **Always backup** before cleanup
2. **Coordinate with team** before force-push
3. **Start with high thresholds** (10MB+)
4. **Test on a clone** if unsure
5. **Update .gitignore** to prevent re-adding

## Documentation

For complete documentation, see:
- [Git Cleanup Guide](GIT-CLEANUP.md) - Full documentation
- Main README - Feature overview
- `pf git-cleanup-help` - Quick reference

## Support

Questions? Issues?
1. Check the documentation
2. Run `pf git-cleanup-help`
3. Review git-filter-repo docs
4. File an issue on GitHub

---

**Ready to clean your repository?** Run `pf git-cleanup` to get started! 🧹
