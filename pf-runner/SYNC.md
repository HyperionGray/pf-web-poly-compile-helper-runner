# pf sync command

A simple, explicit, and safe way to synchronize files locally or over SSH using rsync.

## Why explicit over auto-discovery?

Automatic dependency discovery (e.g., via strace) is noisy and brittle. It often:
- Pulls in transient or system files you do not want
- Misses implicit runtime dependencies
- Makes reproducibility and code review harder

Explicit paths (plus a small manifest) are predictable, reviewable, and secure.

## Grammar

Inside a `task` body:

```
sync key="value" key=["a","b"] flag
```

- Strings support variable substitution from env and task params: `$VAR` or `${VAR}`
- Arrays are JSON-like with quoted strings
- Flags are bare identifiers (boolean true)

## Keys

Required:
- `src`: source path (local)
- `dest`: destination path (local or remote path portion)

Optional:
- `host`: remote host (enables SSH transport)
- `user`: SSH username
- `port`: SSH port
- `excludes`: array of rsync exclude patterns
- `exclude_file`: path to a file with rsync exclude patterns (one per line)
- `delete`: mirror destination by deleting extraneous files
- `dry`: dry-run
- `verbose`: verbose output (default true)

## Examples

Local dry-run sync:

```
# assumes PROJECT_ROOT env defined
sync src="$PROJECT_ROOT/app/static/" dest="$PROJECT_ROOT/data/sync_test/" \
     excludes=["*.pyc","__pycache__/"] dry verbose
```

Remote sync over SSH:

```
sync src="./build/" dest="/var/www/app/" host="example.com" user="deploy" port="2222" \
     excludes=[".git/","node_modules/"] delete
```

Using an exclude file:

```
sync src="./" dest="/srv/app/" host="example.com" exclude_file="./rsync.exclude" dry
```

`rsync.exclude` example:

```
.git/
node_modules/
*.pyc
__pycache__/
.DS_Store
```

## Safety checklist

- Start with `dry` until output looks correct
- Prefer `excludes` / `exclude_file` to avoid syncing junk
- Use `delete` only when you mean to mirror the destination
- Confirm SSH user/host/port before running

## Notes

- This implementation shells out to `rsync` and supports both local and ssh transports
- Variable substitution works on all string values
- If `rsync` is missing, the command will not run and will print an error
