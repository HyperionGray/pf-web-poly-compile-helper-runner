# pf Quickstart (10‑minute tour)

Minimal steps to install, run tasks, and write your own.

## Install
- Build `.deb`: `./deb/build-deb.sh 1.0.0`
- Install: `sudo dpkg -i deb/build/pf-runner_1.0.0.deb && sudo apt-get install -f -y`


Check: `pf list`

## Run a task
```bash
pf hello
pf web-dev port=5173          # params are flexible
pf web-dev --port 5173        # same
pf web-dev --port 5173 env=dev
```
Formats accepted: `key=value`, `--key=value`, `--key value` (mix freely).

## Define a task (bash)
```pf
# Pfyfile.pf

task hello
  describe Print a greeting
  shell echo "Hello from pf"
end
```
Run with `pf hello`.

## Implicit commands (new)
Set a default language once, then omit `shell`:
```pf
default_lang python

task hi-py
  print("hi from python")          # runs as python
  import sys; print(sys.version)
end

task hi-bash default_lang=bash
  echo "hi from bash"              # falls back to bash
end
```
If no `default_lang`, bare lines run in your current shell.
Place `default_lang` at file top (applies to following tasks) or per task via `default_lang=python`.

## Mix languages per line
```pf
task poly
  shell_lang python
  shell print("py line")
  shell_lang bash
  shell echo "back to bash"
  shell [lang:node] console.log('node inline')
end
```

## Env for a task
```pf
task serve
  env PORT=8080 DEBUG=false
  shell echo "PORT=$PORT DEBUG=$DEBUG"
  shell python -m http.server $PORT
end
```
CLI params override env: `pf serve PORT=9000`.

## Aliases
```pf
task deploy [alias d]
  shell echo "deploying $target"
end
```
Call with `pf d target=prod`.

## Multiline commands
Use `\` or heredoc:
```pf
task build
  shell make \
        -j4 \
        VERBOSE=1
end

task script
  shell <<'EOF'
set -e
npm test
npm run build
EOF
end
```

## Includes (split files)
```pf
include Pfyfile.web.pf
include Pfyfile.security.pf
```
Tasks from included files appear as sections in `pf list`.

## Remote targets (quick taste)
```pf
task uptime
  describe Run on many hosts
  shell env=prod host=ubuntu@10.0.0.5:22 uptime
end
```
For full SSH/hosts syntax see docs.

## Smart workflows (one command does it)
```bash
pf smart-analyze target=/path/to/thing   # auto-detect + analyze
pf checksec-unified binary=./a.out       # unified security check
```
See `pf smart-help` for the short menu.

## Troubleshooting quickies
- See tasks: `pf list`
- Run with params help: `pf <task> --help`
- Verbose parsing: `pf --debug list`
- Validate all Pfyfiles: `python run_syntax_check.py`

## What next?
- Smart combos: `docs/SMART-WORKFLOWS.md`
- REST API: `pf rest-dev`
- WebAssembly demos: `pf web-build-all-wasm`
