# pf — tiny Fabric runner (symbol-free DSL)

## Quick Install (One Command)

```bash
# Clone and install pf with completions
cd pf-runner && make setup && make install-local && make install-completions
```

That's it! The `pf` command is now available in your shell with tab completions.

### Alternative Install Methods

**Development/Local:**
```bash
make setup              # Creates ./pf symlink for local use
make install-local      # Installs pf to ~/.local/bin
make install-completions # Installs shell completions (bash & zsh)
```

**System-wide with static binary:**
```bash
make build              # Creates static executable
make install            # Installs to /usr/local/bin with completions (requires sudo)
```


## WHAT IS IT!?

Single-file **Fabric** runner with a tiny, readable DSL, parallel SSH, and live output.

- One file: `pf_parser.py` (or `pf.py`)
- Symbol-free DSL: `shell`, `packages install/remove`, `service start/stop/enable/disable/restart`, `directory`, `copy`, `sync`
- Task metadata: `describe` shows in `pf list`
- Project split: `include` other `.pf` files from `Pfyfile.pf`
- Per-task params: `pf run-tls tls_cert=... port=9443` → use `$tls_cert`, `$port` in DSL
- **Per-task env**: line `env KEY=VAL KEY2=VAL2` applies to the rest of the task
- Host args: `env=prod`, `hosts=user@ip:port,...`, repeatable `host=...`
- **Shell completions**: Automatic task and option completion for bash and zsh

## What's New! 🎉

### Organized Task List Output
Tasks are now automatically **grouped by their source file**, making `pf list` much cleaner:

```bash
$ pf list
Built-ins:
  update  upgrade  install-base  ...

From Pfyfile.pf:
  default-task  setup  install  ...

[shells] From Pfyfile.shells.pf:
  bash-cli  zsh-cli  shell-cli  ...

[tests] From Pfyfile.tests.pf:
  test-basic  test-integration  ...
```

Include files like `Pfyfile.shells.pf` automatically create logical groups with clean section headers!

### Inline Environment Variables in Shell Commands
You can now set environment variables inline in shell commands:

```bash
task my-task
  shell MY_VAR=hello bash -c 'echo $MY_VAR'
  shell PORT=8080 API_KEY=secret ./start-server.sh
  shell DEBUG=1 npm run build
end
```

This properly preserves quoting and passes environment variables to the command.

### pfuck - Autocorrect Failed Commands
Like `thefuck` but specifically for pf tasks! When a task fails due to a typo:

```bash
$ pf orgnaize
[error] no such task: orgnaize — did you mean: organize?

$ pfuck
Last command: pf orgnaize
Failed task: orgnaize

💡 Did you mean one of these?
  1. pf organize
  2. pf upgrade
  ...

Run suggestion #1? [Y/n]:
```

Install pfuck alongside pf for even easier task correction!

## Install

```bash
pip install "fabric>=3.2,<4"
chmod +x pf.py
```

## Quickstart

```bash
pf list
pf env=prod update
pf hosts=ubuntu@10.0.0.5:22,punk@10.4.4.4:24 run-tls tls_cert=$PWD/certs/server.crt tls_key=$PWD/certs/server.key port=9443
```

## Toolchain setup

If you're on an apt-based host and want the polyglot `shell` templates to "just work", run:

```bash
pf setup
```

That installs Java/OpenJDK 25, Google Android build tools (34.0.0), Go, LLVM/clang, Ninja and gfortran. Extra interpreters (LuaJIT, static zsh, ch) plus `rustup` live under a separate opt-in task:

```bash
pf setup-optional
```

Feel free to tweak the package list if your distro uses different names or you want to pin versions.

## Command-Line Syntax & Argument Flexibility

The `pf` command line parser is **flexible about argument order**. You can mix options, parameters, and task names in any order that feels natural:

```bash
# All of these are equivalent:
pf my-task param=value env=prod
pf env=prod my-task param=value
pf param=value env=prod my-task

# Multiple tasks with their own parameters:
pf build release=true test coverage=true

# Environment and host options can appear anywhere:
pf env=staging deploy host=server1.com:22
pf host=server1.com:22 env=staging deploy
```

### Available Command-Line Options

- `env=NAME` - Use a named environment from `ENV_MAP` (can specify multiple)
- `hosts=user@host:port,...` - Connect to specific hosts (comma-separated)
- `host=user@host:port` - Connect to a single host (can specify multiple)
- `user=USERNAME` - Default SSH username
- `port=PORT` - Default SSH port
- `sudo=true` - Run commands with sudo
- `sudo_user=USER` - Run commands as a specific user with sudo

### Shell Compatibility

The DSL is designed to be **shell-friendly**:

- **Variables**: Use `$VAR` or `${VAR}` for variable interpolation
- **Quoting**: Single and double quotes work as expected in shell commands
- **Line continuations**: Backslash `\` works for multi-line commands
- **Environment variables**: Both task-level `env` and system environment variables are supported
- **Parameter passing**: `key=value` pairs work naturally without special escaping

Example with complex shell structures:
```text
task deploy
  env VERSION=1.0.0 ENVIRONMENT=prod
  shell docker build -t myapp:${VERSION} .
  shell docker tag myapp:${VERSION} myapp:latest
  shell if [ "$ENVIRONMENT" = "prod" ]; then \
          docker push myapp:${VERSION}; \
          docker push myapp:latest; \
        fi
end
```

## DSL

```text
task run-tls
  describe Start packetfs-infinity with Hypercorn TLS
  env tls_cert=$PWD/certs/server.crt tls_key=$PWD/certs/server.key port=9443
  shell podman run --rm \
       -p $port:9443 \
       -v $tls_cert:/certs/server.crt:ro \
       -v $tls_key:/certs/server.key:ro \
       packetfs/pfs-infinity:latest
end
```

- `$VAR` / `${VAR}` are interpolated from (in order): **task params** → **task env** → **process env**.
- On remote hosts: `env` is translated to `export VAR=...;` before each command.
- Locally: variables are provided via the process environment.

### Polyglot `shell` overrides

The `shell` verb now accepts a shebang-style inline template to pipe snippets through many common runtimes:

```text
task demo
  shell [lang:python] print("hello from python")
  shell [lang:rust] @scripts/demo.rs -- --flag fast
  shell [lang:java-android] @scripts/android_smoke/Main.java -- --device pixel_8
end
```

You can also pin a language across multiple lines without repeating the inline tag:

```text
task multi
  shell_lang python
  shell print("first")
  shell print("second")
  shell_lang default   # back to whatever the task inherited
  shell echo "done"
end
```

Place `#!lang:python` (or `#!lang:fish`) at the very top of a Pfyfile to set a repository-default language; `shell_lang none` clears the override inside a task.

- Prefix the inline template with `lang:` / `language:` / `polyglot` plus the language name.
- Short snippets can be written inline; for multiline programs use `@path/to/file.ext`.
- `@file -- arg1 arg2` lets you pass CLI args to the generated program.
- All snippets run inside ephemeral temp directories via `mktemp`; artifacts are deleted unless the command fails.
- Supported names (aliases in parentheses): `python (py, python3)`, `bash`, `sh`, `zsh`, `fish`, `lua`, `go (golang)`, `c (clang)`, `c++ (cpp, cxx, clang++)`, `fortran (gfortran, fortran90)`, `asm (asm86)`, `rust`, `swift`, `java-openjdk (java)`, `java-android (java-android-google, android-java)`.
- Officially supported languages remain **python**, **bash**, and **fish**. Using `shell_lang python` / `shell_lang bash` / `shell_lang fish` (or a `#!lang:...` header) ensures those runtimes stay active until you reset or clear them. Everything else is best-effort and simply stitches together available interpreters/compilers (`clang/clang++`, `gfortran`, `go`, `rustc`, `swift`, `javac`, Android SDK `d8`/`dalvikvm`, etc.). Install the toolchains you care about or expect the command to fail loudly.
- `java-android` looks for `ANDROID_SDK_ROOT`/`ANDROID_HOME` plus build-tools (`d8`) and `dalvikvm`. If those aren’t present it falls back to running on the local JVM after compiling against whatever `android.jar` it can find.

Because the snippets expand to real shell scripts, they inherit your `sudo=true`/remote host settings and obey per-task `env` just like regular `shell` lines. Treat this as a "test test runner" sandbox — there are zero safety guarantees when mixing exotic interpreters.

### Language Specification Rules

**IMPORTANT**: When using polyglot shell features, you must specify the language in one of three ways:

1. **Per-command inline**: `shell [lang:python] print("hello")`
2. **Task-level setting**: Use `shell_lang python` at the start of a task
3. **Global/file-level**: Add `#!lang:python` as the first line of your Pfyfile.pf

**Without specifying a language**, commands are executed as regular shell commands (bash by default).

#### Language Scope Hierarchy

Language specifications follow this precedence (highest to lowest):

1. **Inline language tags** `[lang:...]` - Applies to single command only
2. **Task-level `shell_lang`** - Applies to all subsequent commands in the task
3. **File-level shebang** `#!lang:...` - Applies to entire file as default
4. **Environment variable** `PF_SHELL_TEMPLATE` - System-wide default
5. **Built-in default** - Standard bash shell

#### Resetting Language Context

```text
# Set language for a task
task python-heavy
  shell_lang python
  shell print("This runs in Python")
  shell import sys; print(sys.version)
  
  # Reset to default shell
  shell_lang default
  shell echo "Back to bash"
  
  # Or clear completely (same as default)
  shell_lang none
  shell pwd
end

# File-level default
#!lang:python

task task1
  # All shells use Python by default
  shell print("Hello from Python")
end

task task2
  # Override with bash for this task
  shell_lang bash
  shell echo "Hello from bash"
end
```

#### Best Practices

- **Be explicit**: Always specify the language when using polyglot features
- **Minimize context switching**: Group commands of the same language together
- **Document language requirements**: Use `describe` to note language dependencies
- **Test language availability**: Check that required interpreters are installed

Example with clear language specification:
```text
task build-and-test
  describe Build Rust project and run Python tests (requires: rust, python3)
  
  # Rust compilation
  shell_lang rust
  shell @build/compile.rs
  
  # Switch to Python for testing
  shell_lang python
  shell @tests/runner.py
  
  # Back to shell for cleanup
  shell_lang bash
  shell rm -rf target/debug/test-*
end
```

### LLVM IR Output

C, C++, and Fortran can emit LLVM IR instead of executing:

```text
task show-llvm
  shell [lang:c-llvm] int main() { return 42; }
  shell [lang:cpp-llvm] int main() { return 42; }
  shell [lang:fortran-llvm] program hello; end program hello
end
```

Available LLVM variants:
- `c-llvm` / `c-ir` / `c-ll` - C to LLVM IR (text format)
- `cpp-llvm` / `cpp-ir` / `cpp-ll` - C++ to LLVM IR
- `c-llvm-bc` / `c-bc` - C to LLVM bitcode (then disassembled to IR)
- `cpp-llvm-bc` / `cpp-bc` - C++ to LLVM bitcode
- `fortran-llvm` / `fortran-ir` / `fortran-ll` - Fortran to LLVM IR (requires flang)

### File Synchronization with `sync`

The `sync` verb provides rsync-based file synchronization for both local and remote (SSH) transfers:

```text
task backup-local
  describe Sync files locally with excludes
  sync src="/project/src/" dest="/backup/src/" excludes=["*.log","*.tmp"] verbose
end

task deploy-remote
  describe Deploy to remote server
  sync src="./build/" dest="/var/www/app/" host="server.com" user="deploy" port="22" delete
end

task sync-with-file
  describe Sync using exclude file
  sync src="./" dest="/backup/" exclude_file=".rsync-exclude" dry
end
```

**Parameters:**
- `src=<path>` (required) - Source directory path
- `dest=<path>` (required) - Destination directory path
- `host=<host>` - Remote hostname for SSH sync
- `user=<user>` - SSH username
- `port=<port>` - SSH port (default: 22)
- `excludes=["pattern1","pattern2"]` - Array of exclude patterns
- `exclude_file=<path>` - File containing exclude patterns (one per line)
- `delete` - Mirror mode: delete extraneous files in destination
- `dry` - Dry-run mode: show what would be transferred
- `verbose` - Verbose output

All string parameters support variable interpolation (`$VAR` or `${VAR}`). See [SYNC.md](SYNC.md) for complete documentation.

### Build System Helpers

The DSL includes dedicated verbs for common build systems. Use `build_detect` to analyze your project:

```text
task detect
  describe Auto-detect build system
  build_detect
end
```

#### Automagic Builder 🪄

**NEW!** The `autobuild` verb automatically detects your project's build system and runs the appropriate build command with zero configuration:

```text
task quick-build
  describe Build any project automatically
  autobuild
end

task release-build
  describe Release build with auto-detection
  autobuild release=true jobs=8
end

task monorepo-build
  describe Build multiple modules
  autobuild dir=./frontend
  autobuild dir=./backend
  autobuild dir=./shared
end
```

**Supported Build Systems (in priority order):**
1. **Cargo** (Cargo.toml) → `cargo build`
2. **Go** (go.mod) → `go build`
3. **npm** (package.json) → `npm run build` or `npm install`
4. **Python** (setup.py, pyproject.toml) → `pip install -e .` or `python setup.py build`
5. **Maven** (pom.xml) → `mvn compile`
6. **Gradle** (build.gradle) → `gradle build`
7. **CMake** (CMakeLists.txt) → `cmake` + `cmake --build`
8. **Meson** (meson.build) → `meson setup` + `meson compile`
9. **Just** (justfile) → `just`
10. **Autotools** (configure) → `./configure` + `make`
11. **Make** (Makefile) → `make`
12. **Ninja** (build.ninja) → `ninja`

**Parameters:**
- `release=true` - Build in release/optimized mode
- `jobs=N` - Number of parallel jobs (default: 4)
- `dir=<path>` - Build a specific subdirectory
- `target=<target>` - Custom build target (for Make, etc.)

The automagic builder prioritizes specific build systems over generic ones (e.g., CMake over generated Makefiles), ensuring the "source of truth" build system is always used.

#### Makefile

```text
task build
  describe Build with make
  makefile all jobs=4
end

task rebuild
  describe Clean and rebuild
  makefile clean all verbose=true
end
```

Options: `jobs=N`, `parallel=true`, `verbose=true`, plus any `VAR=value` make variables.

#### CMake

```text
task cmake-build
  describe Configure and build with CMake
  cmake . build_dir=build build_type=Release
end
```

Options: `build_dir=<path>`, `build_type=<Debug|Release|...>`, `generator=<Ninja|...>`, `target=<name>`, `jobs=N`, plus any `-D` CMake options as `OPTION=value`.

#### Meson + Ninja

```text
task meson-build
  describe Build with Meson
  meson . build_dir=builddir buildtype=release
end
```

Options: `build_dir=<path>`, `buildtype=<debug|release|...>`, `target=<name>`, plus any `-D` Meson options.

#### Cargo (Rust)

```text
task cargo-build
  describe Build Rust project
  cargo build release=true
end

task cargo-test
  describe Run tests
  cargo test
end
```

Options: `release=true`, `features=<list>`, `target=<triple>`, `manifest_path=<path>`, plus any cargo flags.

#### Go

```text
task go-build
  describe Build Go binary
  go_build output=myapp tags=netgo
end

task go-test
  describe Run Go tests
  go_build subcommand=test race=true
end
```

Options: `subcommand=<build|test|...>`, `output=<path>`, `tags=<list>`, `race=true`, `ldflags=<flags>`.

#### Autotools (Configure)

```text
task configure
  describe Run configure script
  configure prefix=/usr/local shared=true ssl=true
end
```

Options: `prefix=<path>`, `<feature>=true` → `--enable-<feature>`, `<feature>=false` → `--disable-<feature>`, `<opt>=<value>` → `--<opt>=<value>`.

#### Just

```text
task just-build
  describe Run justfile recipe
  justfile build --verbose
end
```

All arguments are passed directly to the `just` command.

## Includes

Top-level in `Pfyfile.pf`:

```text
include "base.pf"
include web.pf
```

## Environments & Hosts

```bash
pf env=prod update
pf env=prod env=staging run
pf hosts=ubuntu@10.0.0.5:22,punk@10.4.4.4:24 down
pf host=ubuntu@10.0.0.5:22 sudo=true upgrade
```

Define env aliases in `ENV_MAP` at the top of `pf.py`:

```python
ENV_MAP = {
  "local": ["@local"],
  "prod": ["ubuntu@10.0.0.5:22", "punk@10.4.4.4:24"],
  "staging": "staging@10.1.2.3:22,staging@10.1.2.4:22",
}
```

## Project Structure

This project uses a modular task organization:

- `Pfyfile.pf` - Main configuration with includes for all task categories
- `Pfyfile.dev.pf` - Development tasks (setup, lint, test, symlink)
- `Pfyfile.tests.pf` - Testing tasks (basic, integration, docs)
- `Pfyfile.builds.pf` - Build and release tasks (validate, package, install)
- `Pfyfile.cleanup.pf` - Cleanup and maintenance tasks
- `base.pf`, `web.pf`, `test.pf` - Core functionality examples
- `scripts/` - Helper scripts (following no-long-commands rule)

## Quick Start Commands

```bash
# Complete project setup
./pf.py setup

# Validate everything works
./pf.py validate

# Run basic functionality tests
./pf.py test-basic

# Clean up project
./pf.py clean-all
```

## Notes

- Uses your SSH agent/keys and `~/.ssh/config` if present
- `packages` assumes **apt**; easy to extend to `dnf`, `pacman`, etc.
- Parallelism: min(32, number of hosts). Tweak in code.
- Follows PODMAN > Docker rule - use `podman_install` instead of `docker_install`
- Helper scripts in `scripts/` directory keep pf files clean and readable


## Polyglot languages (native-linux target)

**Built-in runtimes** via `shell [lang:...]` or `shell_lang ...`:

- asm, bash, c, cpp, crystal, dart, dash, deno, elixir, fish, fortran, go, haskell, haskell-compile, java-android, java-openjdk, julia, ksh, lua, nim, node, ocaml, ocamlc, perl, php, pwsh, python, r, ruby, rust, sh, tcsh, ts-node, zig, zsh

**Aliases** (map → canonical):

- `shell` → `bash`
- `sh` → `sh`
- `zshell` → `zsh`
- `powershell` → `pwsh`
- `ps1` → `pwsh`
- `py` → `python`
- `python3` → `python`
- `ipython` → `python`
- `javascript` → `node`
- `js` → `node`
- `nodejs` → `node`
- `ts` → `deno`
- `typescript` → `deno`
- `tsnode` → `ts-node`
- `c++` → `cpp`
- `cxx` → `cpp`
- `clang` → `c`
- `clang++` → `cpp`
- `g++` → `cpp`
- `gcc` → `c`
- `golang` → `go`
- `rb` → `ruby`
- `pl` → `perl`
- `ml` → `ocaml`
- `hs` → `haskell`
- `fortran90` → `fortran`
- `gfortran` → `fortran`
- `java` → `java-openjdk`
- `java-openjdk` → `java-openjdk`
- `java-android-google` → `java-android`
- `java-android` → `java-android`
- `android-java` → `java-android`
- `fishshell` → `fish`
- `shellscript` → `bash`
- `dashshell` → `dash`