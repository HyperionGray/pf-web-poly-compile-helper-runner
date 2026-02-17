# Package Manager Translation Tool

A comprehensive tool for translating packages between the 5 most common Linux package managers:

- **deb** - Debian/Ubuntu (apt/dpkg)
- **rpm** - Red Hat/Fedora/SUSE (yum/dnf)
- **flatpak** - Cross-distro sandboxed apps
- **snap** - Canonical's universal packages
- **pacman** - Arch Linux

## Key Features

### Hub-Based Conversion

All conversions use `.deb` as the **hub format**. This means:

```
source_format → .deb → target_format
```

For example, converting Flatpak to RPM:
```
flatpak → .deb → rpm
```

This approach ensures:
1. **Consistency**: All conversions go through a well-tested intermediate format
2. **Simplicity**: Only 2 conversion paths needed per format instead of N²
3. **Reliability**: deb format has the most mature tooling

### Conversion Matrix

```
        deb      rpm      flatpak  snap     pacman  
        ---------------------------------------------
deb        -       ✓       ✓       ✓       ✓    
rpm        ✓       -     ✓→deb   ✓→deb   ✓→deb  
flatpak    ✓     ✓→deb     -     ✓→deb   ✓→deb  
snap       ✓     ✓→deb   ✓→deb     -     ✓→deb  
pacman     ✓     ✓→deb   ✓→deb   ✓→deb     -    

Legend: ✓ = direct, ✓→deb = via .deb hub
```

## Quick Start

### Check Available Formats

```bash
pf pkg-formats
```

This shows which package formats are available on your system.

### Convert a Package

```bash
# Convert RPM to DEB
pf pkg-convert source=package.rpm target=deb

# Convert Flatpak to RPM (via .deb hub)
pf pkg-convert source=app.flatpak target=rpm

# Specify output path
pf pkg-convert source=package.rpm target=deb output=/path/to/output.deb
```

### Shorthand Commands

```bash
# Convert to specific formats
pf pkg-convert-to-deb source=package.rpm
pf pkg-convert-to-rpm source=package.deb
pf pkg-convert-to-flatpak source=package.deb
pf pkg-convert-to-snap source=package.deb
pf pkg-convert-to-pacman source=package.deb
```

### Get Package Information

```bash
pf pkg-info package=myapp.deb
```

Output:
```
Package Information:

Name:        myapp
Version:     1.0.0
Architecture: amd64
Description: My Application
Format:      deb

Dependencies:
  - libc6 (>= 2.17)
  - libssl1.1

Files: (15 total)
  /usr/bin/myapp
  /usr/share/myapp/...
```

### Check Dependencies

```bash
pf pkg-deps package=myapp.rpm target=deb
```

This shows which dependencies are:
- Already satisfied on the target system
- Missing and need to be installed

## CLI Usage

You can also use the tool directly:

```bash
# Show help
node tools/package-manager.mjs --help

# Convert a package
node tools/package-manager.mjs convert source.rpm deb

# Get package info
node tools/package-manager.mjs info package.deb

# Check dependencies
node tools/package-manager.mjs deps package.rpm deb

# Show available formats
node tools/package-manager.mjs formats

# Show conversion matrix
node tools/package-manager.mjs matrix
```

## Installing Required Tools

### For All Formats

```bash
pf install-pkg-tools
```

This installs:
- dpkg-dev (for deb)
- rpm/rpm-build (for rpm)
- alien (cross-format tool)
- squashfs-tools (for snap)
- zstd (for pacman)

### For Flatpak

```bash
pf install-flatpak
```

### For Snap

```bash
pf install-snap
```

## Dependency Management

The tool properly handles dependencies during conversion:

1. **Extraction**: Reads dependencies from source package
2. **Translation**: Maps dependency names between formats when possible
3. **Verification**: Checks if dependencies exist in target format

### Check Dependencies Before Conversion

```bash
pf pkg-check-deps package=myapp.rpm target=deb
```

### Install Missing Dependencies

```bash
pf pkg-install-deps package=myapp.rpm target=deb
```

## Batch Conversion

Convert multiple packages at once:

```bash
pf pkg-batch-convert packages="pkg1.rpm pkg2.rpm pkg3.rpm" target=deb
```

## Examples

### Example 1: Convert RPM to DEB

```bash
$ pf pkg-convert source=nginx-1.24.0.rpm target=deb

⠋ Detecting source format...
✔ Source format: rpm
⠋ Extracting package information...
⠋ Extracting package contents...
⠋ Creating deb package...
✔ Converted rpm → deb: nginx_1.24.0_amd64.deb
```

### Example 2: Convert Snap to RPM (via hub)

```bash
$ pf pkg-convert source=myapp.snap target=rpm

⠋ Detecting source format...
✔ Source format: snap
⠋ Extracting package information...
⠋ Extracting package contents...
⠋ Converting snap → deb (hub format)...
⠋ Creating rpm package...
✔ Converted snap → rpm: myapp-1.0.x86_64.rpm
```

### Example 3: Inspect Package Before Conversion

```bash
$ pf pkg-info package=vscode.deb

Package Information:

Name:        code
Version:     1.84.2
Architecture: amd64
Description: Visual Studio Code
Format:      deb

Dependencies:
  - libc6 (>= 2.17)
  - libgtk-3-0 (>= 3.10)
  - libnss3 (>= 3.26)
  - libxss1

Files: (1847 total)
  /usr/share/code/...
```

## Architecture Mapping

The tool automatically maps architectures between formats:

| Debian (deb) | RPM | Pacman |
|--------------|-----|--------|
| amd64 | x86_64 | x86_64 |
| i386 | i686 | i686 |
| all | noarch | any |
| arm64 | aarch64 | aarch64 |

## Limitations

1. **Sandboxing**: Flatpak and Snap have unique sandboxing features that can't be fully preserved when converting to other formats.

2. **Desktop Integration**: Some package-specific features (like Snap interfaces or Flatpak permissions) may not translate.

3. **Dependencies**: Dependency names may differ between distributions. The tool attempts to map them, but manual intervention may be needed.

4. **Build Systems**: Some packages require specific build environments. Pre-built binaries convert best.

## Troubleshooting

### "Format not available"

Install the required tools:
```bash
pf install-pkg-tools
pf install-flatpak
pf install-snap
```

### Dependencies Not Found

The tool tries to map dependencies, but some may not have equivalents:
1. Check if a similar package exists with a different name
2. Install the missing dependency manually
3. Re-run the dependency check

### Conversion Fails

1. Check if the source package is valid: `pf pkg-info package=...`
2. Ensure all required tools are installed: `pf pkg-formats`
3. Try converting to deb first, then to target format

## API Usage

For programmatic usage, import the module:

```javascript
import { 
  PackageConverter, 
  PackageInfo,
  SUPPORTED_FORMATS 
} from './tools/package-manager.mjs';

const converter = new PackageConverter();

// Check available formats
const formats = converter.getAvailableFormats();

// Detect format
const format = converter.detectFormat('package.rpm');

// Get package info
const info = await converter.getInfo('package.deb');

// Convert package
const output = await converter.convert('input.rpm', 'deb', 'output.deb');

// Resolve dependencies
const deps = await converter.resolveDependencies('package.rpm', 'deb');
```

## pf Tasks Reference

| Task | Description |
|------|-------------|
| `pf pkg-convert` | Convert a package between formats |
| `pf pkg-convert-to-deb` | Convert any package to .deb |
| `pf pkg-convert-to-rpm` | Convert any package to .rpm |
| `pf pkg-convert-to-flatpak` | Convert any package to .flatpak |
| `pf pkg-convert-to-snap` | Convert any package to .snap |
| `pf pkg-convert-to-pacman` | Convert any package to .pkg.tar.zst |
| `pf pkg-info` | Display package information |
| `pf pkg-deps` | Resolve dependencies for target format |
| `pf pkg-formats` | Show available formats |
| `pf pkg-matrix` | Show conversion matrix |
| `pf pkg-help` | Show help |
| `pf install-pkg-tools` | Install conversion tools |
| `pf install-flatpak` | Install Flatpak |
| `pf install-snap` | Install Snapd |
| `pf pkg-batch-convert` | Convert multiple packages |
| `pf pkg-check-deps` | Check dependencies |
| `pf pkg-install-deps` | Install missing dependencies |

## Contributing

To add support for a new package format:

1. Create a handler class extending `PackageFormatHandler`
2. Implement the required methods:
   - `isAvailable()`: Check if tools are installed
   - `extractInfo(path)`: Extract package metadata
   - `extractContents(path, dir)`: Extract files
   - `createPackage(dir, info, output)`: Create package
3. Add the format to `SUPPORTED_FORMATS`
4. Register the handler in `PackageConverter`
5. Add tests and documentation

## License

See the project LICENSE file.
