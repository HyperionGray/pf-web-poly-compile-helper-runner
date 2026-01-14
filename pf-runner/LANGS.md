# pf-runner polyglot languages (native-linux)

The `shell` verb now supports many languages via inline `[lang:xxx]` or task-wide `shell_lang`.

**NEW**: When `shell_lang` is set, you can omit the `shell` prefix for cleaner, more readable tasks!

## Supported languages

- bash, sh, dash, zsh, fish, ksh, tcsh, pwsh
- python, node, deno, ts-node, perl, php, ruby, r, julia, haskell, ocaml, elixir, dart, lua
- go, rust, c, cpp, fortran, asm, zig, nim, crystal, haskell-compile, ocamlc
- java-openjdk, java-android

## LLVM IR Output

- c-llvm, cpp-llvm, fortran-llvm - Generate LLVM IR (text format)
- c-llvm-bc, cpp-llvm-bc - Generate LLVM bitcode and disassemble to IR

## Aliases

See README section "Polyglot languages (native-linux target)" for full alias list.

LLVM aliases:
- c-ir, c-ll → c-llvm
- cpp-ir, cpp-ll → cpp-llvm
- c-bc → c-llvm-bc
- cpp-bc → cpp-llvm-bc
- fortran-ll, fortran-ir → fortran-llvm

## Examples

### Old Style (Still Supported)
```text
task demo-old
  shell [lang:bash] echo hello
  shell [lang:python] print("hi")
  shell [lang:node] console.log("yo")
  shell [lang:pwsh] Write-Output 'ok'
  shell [lang:c-llvm] int main() { return 42; }
end

task multi-old
  shell_lang python
  shell print("one")
  shell print("two")
  shell_lang default
  shell echo "back to default shell"
end
```

### NEW: Cleaner Syntax (Recommended)
```text
task demo-new
  shell_lang bash
  echo hello
  
  shell [lang:python] print("hi")      # Inline override
  shell [lang:node] console.log("yo")  # Inline override
  
  echo "back to bash"
end

task build-project
  shell_lang bash
  echo "Building project..."
  cd src && make clean
  make all -j$(nproc)
  echo "Build complete!"
end

task python-script
  shell_lang python
  import sys
  print(f"Python {sys.version}")
  print("Running analysis...")
  # Multiple Python commands without 'shell' prefix!
end

task mixed-languages
  shell_lang bash
  echo "Step 1: Bash commands"
  ls -la
  
  shell [lang:python] print("Step 2: Quick Python")
  
  echo "Step 3: Back to Bash"
  pwd
end
```

## Key Features

1. **Set once, use everywhere**: Use `shell_lang xxx` at the start of a task
2. **Omit `shell` prefix**: Write commands directly after setting `shell_lang`
3. **Inline overrides**: Use `shell [lang:xxx] ...` to temporarily switch languages
4. **Backward compatible**: Old explicit `shell` syntax still works
5. **Clear errors**: Helpful messages if you forget to set `shell_lang`

## Switching Languages

```text
task language-demo
  # Start with bash
  shell_lang bash
  echo "Using bash"
  pwd
  
  # Switch to Python
  shell_lang python
  print("Now using Python!")
  import os; print(f"CWD: {os.getcwd()}")
  
  # Switch back to default shell
  shell_lang default
  shell echo "Back to default"
end
```

## Best Practices

1. **Use `shell_lang`** for tasks with multiple commands in the same language
2. **Use inline `[lang:xxx]`** for one-off commands in a different language
3. **Keep it simple**: If all commands are bash, just use `shell_lang bash`
4. **Be explicit when needed**: Mixed-language tasks benefit from clear language markers
