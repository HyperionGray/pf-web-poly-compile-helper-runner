# Copilot Instructions (P4X-ng)

These instructions apply to all code changes, PRs, and issue work produced by Copilot.

## Global rules
- Follow repository rules and any `rules.json` strictly when present.
- Keep files small and modular (aim for <= 200–300 lines per file). Refactor into multiple files/modules when needed.
- Prefer clarity, safety, and maintainability over cleverness.
- Add or update tests for any significant logic change. Do not reduce test coverage.

## Language choices
- Prefer **Python** if no language is specified.
- If significant JavaScript is required, use **TypeScript** (not JavaScript).
- In C/C++: prioritize memory safety. Add bounds checks; validate pointers; avoid undefined behavior.

## Python standards
- Keep modules small and focused.
- Double-check imports; remove unused imports.
- Use type hints where practical.

## Container / runtime standards
- Use **Podman**, not Docker.
- Name compose files generically according to best practices (e.g., `compose.yml`). Avoid `Dockerfile` unless explicitly required.

## Virtual machines
- For VM needs, use `P4X-ng/HGWS` and the **VMKit** directory.
- If VMKit is missing/broken, fix VMKit first, then proceed.

## Testing / PF DSL
- If tests require PF, use `HyperionGray/pf-web-poly-compiler-helper`.
- Before editing PF scripts, inspect the `.lark` grammar, learn the DSL, and update any examples accordingly.
- Always check `Pfyfile.pf` and other `.pf` files for outdated paths or stale targets; update them.

## Repository cleanup
- As a final step, clean up the repository:
  - Move truly unneeded artifacts to `bak/` at repo root.
  - Move useful references to `refs/` at repo root.
  - Keep the tree tidy and consistent.
