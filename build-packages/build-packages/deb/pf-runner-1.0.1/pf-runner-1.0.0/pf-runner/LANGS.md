# pf-runner polyglot languages (native-linux)

The `shell` verb now supports many languages via inline `lang:` or task-wide `shell_lang`.

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

```text
task demo
  shell [lang:bash] echo hello
  shell [lang:python] print("hi")
  shell [lang:node] console.log("yo")
  shell [lang:pwsh] Write-Output 'ok'
  shell [lang:c-llvm] int main() { return 42; }
end

task multi
  shell_lang python
  shell print("one")
  shell print("two")
  shell_lang default
  shell echo "back to default shell"
end
```
