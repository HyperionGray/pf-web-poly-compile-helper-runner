# pf-runner polyglot languages (native-linux)

The `shell` verb now supports many languages via inline `lang:` or task-wide `shell_lang`.

## Supported languages

- bash, sh, dash, zsh, fish, ksh, tcsh, pwsh
- python, node, deno, ts-node, perl, php, ruby, r, julia, haskell, ocaml, elixir, dart, lua
- go, rust, c, cpp, fortran, asm, zig, nim, crystal, haskell-compile, ocamlc
- java-openjdk, java-android

## Aliases

See README section "Polyglot languages (native-linux target)".

## Examples

```text
task demo
  shell [lang:bash] echo hello
  shell [lang:python] print("hi")
  shell [lang:node] console.log("yo")
  shell [lang:pwsh] Write-Output 'ok'
end

task multi
  shell_lang python
  shell print("one")
  shell print("two")
  shell_lang default
  shell echo "back to default shell"
end
```
