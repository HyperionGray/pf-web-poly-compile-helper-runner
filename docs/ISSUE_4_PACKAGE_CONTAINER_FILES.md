# Issue #4: Test Package Manager and Container Installation .pf Files

## Summary
Test and validate package management and container-related installation .pf files.

## Description
This issue tracks testing of .pf files that handle package management, container builds, and distribution-specific installations:

### Files to Test
1. **Pfyfile.package-manager.pf** - Package format translation and installation
2. **Pfyfile.containers.pf** - Container image building and management
3. **Pfyfile.distro-switch.pf** - Multi-distro package installation
4. **Pfyfile.os-containers.pf** - OS-specific container management
5. **Pfyfile.pe-containers.pf** - PE/Windows container management

### Tasks to Validate

#### Package Manager (Pfyfile.package-manager.pf)
- [ ] `install-pkg-tools` - Install alien, fpm, flatpak-builder
- [ ] `install-flatpak` - Install Flatpak package manager
- [ ] `install-snap` - Install Snapd
- [ ] `pkg-convert` - Convert between package formats
- [ ] `pkg-info` - Display package information

#### Container Management (Pfyfile.containers.pf)
- [ ] `container-build-all` - Build all container images
- [ ] `container-build-base` - Build base Ubuntu image
- [ ] `container-build-pf-runner` - Build pf-runner image
- [ ] `container-build-api` - Build API server images
- [ ] `container-build-compilers` - Build compiler images
- [ ] `container-build-debugger` - Build debugger images

#### Distro Containers (Pfyfile.distro-switch.pf)
- [ ] `distro-install-fedora` - Install packages from Fedora
- [ ] `distro-install-centos` - Install packages from CentOS
- [ ] `distro-install-arch` - Install packages from Arch
- [ ] `distro-install-opensuse` - Install packages from openSUSE
- [ ] `distro-build-all` - Build all distro containers
- [ ] `distro-status` - Show distro container status

#### OS Containers (Pfyfile.os-containers.pf)
- [ ] `os-container-build` - Build OS-specific containers
- [ ] `os-container-status` - Check container status

### Testing Requirements

1. **Syntax Validation**
   - [ ] All package/container .pf files parse correctly
   - [ ] Container runtime commands are valid
   - [ ] Package manager commands are properly formatted

2. **Task Dependencies**
   - [ ] Container build tasks have proper order
   - [ ] Base images are built before dependent images
   - [ ] Package dependencies are resolved

3. **Runtime Detection**
   - [ ] Tasks detect podman/docker availability
   - [ ] Appropriate error messages for missing runtime
   - [ ] Fallback behavior is documented

4. **Package Format Support**
   - [ ] All supported formats are documented
   - [ ] Conversion matrix is accurate
   - [ ] Format detection works correctly

5. **Container Builds**
   - [ ] Dockerfiles exist for all container tasks
   - [ ] Build context is correct
   - [ ] Image tags are properly specified

### Test Commands
```bash
# Test syntax
pf --file Pfyfile.package-manager.pf list
pf --file Pfyfile.containers.pf list
pf --file Pfyfile.distro-switch.pf list

# Test task discovery
pf list | grep -E "(pkg|container|distro)"

# Check help commands
pf pkg-help
pf container-help
pf distro-help

# Non-invasive checks
pf pkg-formats
pf pkg-matrix
pf distro-status
pf container-status 2>/dev/null || echo "Container check skipped"
```

### Expected Results
- All package/container .pf files parse successfully
- All tasks are discoverable and properly categorized
- Container runtime detection works correctly
- Package format support is documented
- Help commands are comprehensive

### Priority
🟡 **Medium** - Important for advanced users and multi-platform support

### Related Files
- `Pfyfile.package-manager.pf`
- `Pfyfile.containers.pf`
- `Pfyfile.distro-switch.pf`
- `Pfyfile.os-containers.pf`
- `Pfyfile.pe-containers.pf`
- `containers/dockerfiles/*.dockerfile`
- `podman-compose.yml`
- `docker-compose.yml`
- `docs/PACKAGE-MANAGER.md`
- `docs/DISTRO-CONTAINER-MANAGEMENT.md`
- `containers/README.md`

### Test Script
Run the automated test:
```bash
./test_install_pf_files.sh
```

### Acceptance Criteria
- [ ] All package/container .pf files pass syntax validation
- [ ] Container build tasks are properly ordered
- [ ] Package conversion tasks are functional
- [ ] Runtime detection works correctly
- [ ] Help commands are comprehensive
- [ ] No parsing or syntax errors
- [ ] Docker/Podman commands are valid
