# PE execution guide
The PE module exposes staged workflows for running Windows Portable Executable binaries and related VM-backed execution flows through a dedicated module entrypoint:
```text
pf pe <task>
```
The module is defined in `pf-files/Pfyfile.pe.pf` and keeps its own task surface isolated from the root `Pfyfile.pf` commands.
## Quick start
List the available PE entrypoints:
```bash
pf pe install-windows-server
pf pe usage
```
Install or verify the basic PE prerequisites:
```bash
pf pe install
```
That quick-start path delegates to the ReactOS build/setup flow, which is the lightest supported path for getting a PE-capable environment ready.
If you want the explicit per-environment install/setup entrypoints, use:
```bash
pf pe install-reactos
pf pe install-windows-server
pf pe install-windows-nano
pf pe install-vmkit
pf pe install-all
```
## Common workflows
### 1. Default Windows PE execution
Run a PE file through the default staged Windows flow:
```bash
pf pe execute pe_file=/absolute/path/to/app.exe
```
This delegates to the Windows Server Core-backed executor.
### 2. ReactOS flow
Build/setup the ReactOS environment and run a PE file:
```bash
pf pe install-reactos
pf pe run-reactos pe=/absolute/path/to/app.exe
```
Use this when you want the ReactOS VM-backed route and the shared host output directory.
### 3. VMKit flow
Prepare the VMKit environment and run or analyze a PE file:
```bash
pf pe install-vmkit
pf pe run-vmkit pe=/absolute/path/to/app.exe
pf pe analyze-vmkit pe=/absolute/path/to/app.exe
```
### 4. Windows image variants
Run against the explicitly staged Windows images:
```bash
pf pe execute-windows pe_file=/absolute/path/to/app.exe
pf pe install-windows-nano
pf pe execute-nano pe_file=/absolute/path/to/app.exe
```
`execute-nano` requires a Nano Server VHDX made available to the container flow.
### 5. macOS binary execution
The same module also exposes a staged macOS QEMU path:
```bash
pf pe build-macos-qemu
pf pe setup-macos
pf pe run-macos-headless
pf pe execute-macos binary_file=/absolute/path/to/macos-binary
```
The macOS flow prints a legal notice at runtime; make sure your usage complies with the applicable Apple license terms.
## Build and preparation tasks
The top-level PE module groups the build and prepare steps so they can be discovered from `pf pe usage`.
### Build staged images
```bash
pf pe build-all
pf pe build-windows-server
pf pe build-windows-nano
pf pe build-reactos
pf pe build-macos-qemu
pf pe build-vmkit
```
### Prepare or set up runtime environments
```bash
pf pe prepare-windows
pf pe prepare-windows-nano
pf pe prepare-reactos
pf pe prepare-macos
pf pe setup-reactos
pf pe setup-vmkit
pf pe setup-macos
```
## Host directories used by the PE flows
Several PE tasks create or mount working directories relative to the current working directory:
- `windows-images/` — Windows Server Core and Nano template assets
- `reactos-images/` — ReactOS images and setup artifacts
- `vmkit-images/` — VMKit image storage
- `macos-images/` — macOS QEMU disk images
- `pe-output/` — output/artifact directory produced by the Windows, ReactOS, and VMKit helper scripts
The Windows, ReactOS, and VMKit helper scripts mount the specific input file directory plus these output/image directories into the container, instead of mounting the whole repository.
## Prerequisites and runtime expectations
- A container runtime compatible with the tasks, typically Podman (`CONTAINER_RT` can override where supported)
- Access to `/dev/kvm` for the VM-backed flows
- Built images for the target path you intend to use
- Absolute or otherwise valid local paths for `pe_file=`, `pe=`, or `binary_file=` parameters
## Useful discovery commands
```bash
pf --file pf-files/Pfyfile.pe.pf list
pf pe usage
pf pe shell-reactos
pf pe shell-vmkit
```
Use the direct `--file` form when you want to inspect just the PE module task surface without the root entrypoint.
## Related files
- `pf-files/Pfyfile.pe.pf`
- `pf-files/mult-exec/Pfyfile.pe-execution.pf`
- `pf-files/mult-exec/Pfyfile.pe-containers.pf`
- `scripts/pe/windows-server-run.sh`
- `scripts/pe/windows-nano-run.sh`
- `scripts/pe/reactos-run.sh`
- `scripts/pe/reactos-setup.sh`
- `scripts/pe/reactos-analyze.sh`
- `scripts/pe/vmkit-setup.sh`
- `scripts/pe/vmkit-run.sh`
- `scripts/pe/vmkit-analyze.sh`
