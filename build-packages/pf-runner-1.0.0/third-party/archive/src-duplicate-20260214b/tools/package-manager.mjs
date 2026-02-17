#!/usr/bin/env node
/**
 * Package Manager Translation Tool
 * 
 * Translates packages between the 5 most common package managers:
 * - deb (Debian/Ubuntu - apt/dpkg)
 * - rpm (Red Hat/Fedora/SUSE - yum/dnf)
 * - flatpak (Cross-distro sandboxed apps)
 * - snap (Canonical's universal packages)
 * - pacman (Arch Linux)
 * 
 * Uses .deb as a hub format for translations:
 * source → .deb → target
 */

import chalk from 'chalk';
import { spawn, execSync } from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import ora from 'ora';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Constants
const MAX_BUFFER_SIZE = 50 * 1024 * 1024;
const SUPPORTED_FORMATS = ['deb', 'rpm', 'flatpak', 'snap', 'pacman'];

/**
 * Execute a command and return output
 */
function execCommand(cmd, cwd = process.cwd(), options = {}) {
  try {
    return execSync(cmd, { 
      cwd, 
      encoding: 'utf-8', 
      maxBuffer: MAX_BUFFER_SIZE,
      stdio: options.silent ? 'pipe' : undefined,
      ...options 
    }).trim();
  } catch (error) {
    if (options.throwOnError !== false) {
      throw new Error(`Command failed: ${cmd}\n${error.message}`);
    }
    return null;
  }
}

/**
 * Check if a command exists on the system
 */
function commandExists(cmd) {
  try {
    execSync(`which ${cmd}`, { encoding: 'utf-8', stdio: 'pipe' });
    return true;
  } catch {
    return false;
  }
}

/**
 * Package information structure
 */
class PackageInfo {
  constructor(data = {}) {
    this.name = data.name || '';
    this.version = data.version || '';
    this.architecture = data.architecture || 'all';
    this.description = data.description || '';
    this.dependencies = data.dependencies || [];
    this.provides = data.provides || [];
    this.conflicts = data.conflicts || [];
    this.maintainer = data.maintainer || '';
    this.homepage = data.homepage || '';
    this.license = data.license || '';
    this.size = data.size || 0;
    this.sourceFormat = data.sourceFormat || '';
    this.files = data.files || [];
  }

  toJSON() {
    return {
      name: this.name,
      version: this.version,
      architecture: this.architecture,
      description: this.description,
      dependencies: this.dependencies,
      provides: this.provides,
      conflicts: this.conflicts,
      maintainer: this.maintainer,
      homepage: this.homepage,
      license: this.license,
      size: this.size,
      sourceFormat: this.sourceFormat,
      files: this.files
    };
  }
}

/**
 * Base class for package format handlers
 */
class PackageFormatHandler {
  constructor(format) {
    this.format = format;
  }

  /**
   * Check if this format's tools are available
   */
  isAvailable() {
    throw new Error('Not implemented');
  }

  /**
   * Extract package information from a package file
   */
  async extractInfo(packagePath) {
    throw new Error('Not implemented');
  }

  /**
   * Extract package contents to a directory
   */
  async extractContents(packagePath, targetDir) {
    throw new Error('Not implemented');
  }

  /**
   * Create a package from a directory with package info
   */
  async createPackage(sourceDir, info, outputPath) {
    throw new Error('Not implemented');
  }

  /**
   * Install a package
   */
  async install(packagePath) {
    throw new Error('Not implemented');
  }

  /**
   * List installed packages
   */
  async listInstalled() {
    throw new Error('Not implemented');
  }

  /**
   * Get info about an installed package
   */
  async getInstalledInfo(packageName) {
    throw new Error('Not implemented');
  }
}

/**
 * DEB format handler (Debian/Ubuntu)
 */
class DebHandler extends PackageFormatHandler {
  constructor() {
    super('deb');
  }

  isAvailable() {
    return commandExists('dpkg') && commandExists('dpkg-deb');
  }

  async extractInfo(packagePath) {
    const controlOutput = execCommand(`dpkg-deb -f "${packagePath}"`, undefined, { throwOnError: false });
    if (!controlOutput) {
      throw new Error(`Failed to extract info from ${packagePath}`);
    }

    const info = new PackageInfo({ sourceFormat: 'deb' });
    
    const lines = controlOutput.split('\n');
    let currentField = '';
    
    for (const line of lines) {
      if (line.startsWith(' ')) {
        // Continuation of previous field
        if (currentField === 'description') {
          info.description += '\n' + line.trim();
        }
      } else {
        const match = line.match(/^([^:]+):\s*(.*)$/);
        if (match) {
          const [, field, value] = match;
          currentField = field.toLowerCase();
          
          switch (currentField) {
            case 'package':
              info.name = value;
              break;
            case 'version':
              info.version = value;
              break;
            case 'architecture':
              info.architecture = value;
              break;
            case 'description':
              info.description = value;
              break;
            case 'depends':
              info.dependencies = this.parseDependencies(value);
              break;
            case 'provides':
              info.provides = value.split(',').map(p => p.trim()).filter(Boolean);
              break;
            case 'conflicts':
              info.conflicts = value.split(',').map(p => p.trim()).filter(Boolean);
              break;
            case 'maintainer':
              info.maintainer = value;
              break;
            case 'homepage':
              info.homepage = value;
              break;
          }
        }
      }
    }

    // Get installed size
    const sizeOutput = execCommand(`dpkg-deb -I "${packagePath}" | grep "Installed-Size"`, undefined, { throwOnError: false });
    if (sizeOutput) {
      const sizeMatch = sizeOutput.match(/Installed-Size:\s*(\d+)/);
      if (sizeMatch) {
        info.size = parseInt(sizeMatch[1]) * 1024; // Convert to bytes
      }
    }

    // Get file list
    const filesOutput = execCommand(`dpkg-deb -c "${packagePath}"`, undefined, { throwOnError: false });
    if (filesOutput) {
      info.files = filesOutput.split('\n')
        .map(line => {
          const match = line.match(/^\S+\s+\S+\s+\d+\s+[\d-]+\s+[\d:]+\s+(.+)$/);
          return match ? match[1] : null;
        })
        .filter(Boolean);
    }

    return info;
  }

  parseDependencies(depString) {
    if (!depString) return [];
    return depString
      .split(',')
      .map(dep => {
        // Parse dependency with version constraints
        const match = dep.trim().match(/^([^\s(]+)(?:\s*\(([^)]+)\))?/);
        if (match) {
          return {
            name: match[1].trim(),
            version: match[2] || null
          };
        }
        return null;
      })
      .filter(Boolean);
  }

  async extractContents(packagePath, targetDir) {
    fs.mkdirSync(targetDir, { recursive: true });
    execCommand(`dpkg-deb -x "${packagePath}" "${targetDir}"`);
    
    // Also extract control files
    const controlDir = path.join(targetDir, 'DEBIAN');
    fs.mkdirSync(controlDir, { recursive: true });
    execCommand(`dpkg-deb -e "${packagePath}" "${controlDir}"`);
    
    return targetDir;
  }

  async createPackage(sourceDir, info, outputPath) {
    // Create DEBIAN control file
    const controlDir = path.join(sourceDir, 'DEBIAN');
    fs.mkdirSync(controlDir, { recursive: true });

    const controlContent = [
      `Package: ${info.name}`,
      `Version: ${info.version}`,
      `Architecture: ${info.architecture}`,
      `Maintainer: ${info.maintainer || 'Package Converter <noreply@example.com>'}`,
      `Description: ${info.description || 'Converted package'}`,
    ];

    if (info.dependencies.length > 0) {
      const deps = info.dependencies.map(d => 
        d.version ? `${d.name} (${d.version})` : d.name
      ).join(', ');
      controlContent.push(`Depends: ${deps}`);
    }

    if (info.provides.length > 0) {
      controlContent.push(`Provides: ${info.provides.join(', ')}`);
    }

    if (info.conflicts.length > 0) {
      controlContent.push(`Conflicts: ${info.conflicts.join(', ')}`);
    }

    if (info.homepage) {
      controlContent.push(`Homepage: ${info.homepage}`);
    }

    fs.writeFileSync(
      path.join(controlDir, 'control'),
      controlContent.join('\n') + '\n'
    );

    // Build the package
    execCommand(`dpkg-deb --build "${sourceDir}" "${outputPath}"`);
    
    return outputPath;
  }

  async install(packagePath) {
    execCommand(`sudo dpkg -i "${packagePath}"`);
  }

  async listInstalled() {
    const output = execCommand('dpkg -l | tail -n +6', undefined, { throwOnError: false });
    if (!output) return [];

    return output.split('\n')
      .map(line => {
        const parts = line.trim().split(/\s+/);
        if (parts.length >= 3 && parts[0].startsWith('ii')) {
          return {
            name: parts[1],
            version: parts[2],
            architecture: parts[3] || 'all'
          };
        }
        return null;
      })
      .filter(Boolean);
  }

  async getInstalledInfo(packageName) {
    const output = execCommand(`dpkg -s "${packageName}"`, undefined, { throwOnError: false });
    if (!output) return null;

    const info = new PackageInfo({ sourceFormat: 'deb' });
    const lines = output.split('\n');

    for (const line of lines) {
      const match = line.match(/^([^:]+):\s*(.*)$/);
      if (match) {
        const [, field, value] = match;
        switch (field.toLowerCase()) {
          case 'package':
            info.name = value;
            break;
          case 'version':
            info.version = value;
            break;
          case 'architecture':
            info.architecture = value;
            break;
          case 'description':
            info.description = value;
            break;
          case 'depends':
            info.dependencies = this.parseDependencies(value);
            break;
        }
      }
    }

    return info;
  }
}

/**
 * RPM format handler (Red Hat/Fedora/SUSE)
 */
class RpmHandler extends PackageFormatHandler {
  constructor() {
    super('rpm');
  }

  isAvailable() {
    return commandExists('rpm') || commandExists('rpm2cpio');
  }

  async extractInfo(packagePath) {
    const info = new PackageInfo({ sourceFormat: 'rpm' });

    // Use rpm command to query package info
    const queryFormat = '%{NAME}|%{VERSION}|%{ARCH}|%{SUMMARY}|%{LICENSE}|%{URL}|%{SIZE}';
    const output = execCommand(
      `rpm -qp --queryformat '${queryFormat}' "${packagePath}"`,
      undefined,
      { throwOnError: false }
    );

    if (output) {
      const [name, version, arch, summary, license, url, size] = output.split('|');
      info.name = name || '';
      info.version = version || '';
      info.architecture = this.convertArch(arch) || 'all';
      info.description = summary || '';
      info.license = license || '';
      info.homepage = url || '';
      info.size = parseInt(size) || 0;
    }

    // Get dependencies
    const depsOutput = execCommand(
      `rpm -qp --requires "${packagePath}"`,
      undefined,
      { throwOnError: false }
    );

    if (depsOutput) {
      info.dependencies = depsOutput
        .split('\n')
        .filter(line => !line.startsWith('rpmlib(') && line.trim())
        .map(dep => {
          const match = dep.match(/^([^\s]+)(?:\s*([<>=]+)\s*(.+))?$/);
          if (match) {
            return {
              name: match[1],
              version: match[2] && match[3] ? `${match[2]} ${match[3]}` : null
            };
          }
          return { name: dep.trim(), version: null };
        });
    }

    // Get provides
    const providesOutput = execCommand(
      `rpm -qp --provides "${packagePath}"`,
      undefined,
      { throwOnError: false }
    );

    if (providesOutput) {
      info.provides = providesOutput.split('\n').filter(Boolean).map(p => p.split(' ')[0]);
    }

    // Get file list
    const filesOutput = execCommand(
      `rpm -qpl "${packagePath}"`,
      undefined,
      { throwOnError: false }
    );

    if (filesOutput) {
      info.files = filesOutput.split('\n').filter(Boolean);
    }

    return info;
  }

  convertArch(rpmArch) {
    const archMap = {
      'x86_64': 'amd64',
      'i386': 'i386',
      'i686': 'i386',
      'noarch': 'all',
      'aarch64': 'arm64'
    };
    return archMap[rpmArch] || rpmArch;
  }

  convertArchToRpm(debArch) {
    const archMap = {
      'amd64': 'x86_64',
      'i386': 'i686',
      'all': 'noarch',
      'arm64': 'aarch64'
    };
    return archMap[debArch] || debArch;
  }

  async extractContents(packagePath, targetDir) {
    fs.mkdirSync(targetDir, { recursive: true });
    
    // Use rpm2cpio to extract contents
    execCommand(`cd "${targetDir}" && rpm2cpio "${packagePath}" | cpio -idmv 2>/dev/null`);
    
    return targetDir;
  }

  async createPackage(sourceDir, info, outputPath) {
    // Create RPM spec file
    const specDir = path.join(sourceDir, 'SPECS');
    const buildRoot = path.join(sourceDir, 'BUILDROOT');
    
    fs.mkdirSync(specDir, { recursive: true });
    fs.mkdirSync(buildRoot, { recursive: true });

    const specContent = `
Name: ${info.name}
Version: ${info.version.replace(/-/g, '_')}
Release: 1
Summary: ${info.description.split('\n')[0] || 'Converted package'}
License: ${info.license || 'Unknown'}
URL: ${info.homepage || 'https://example.com'}
BuildArch: ${this.convertArchToRpm(info.architecture)}

%description
${info.description || 'Package converted from another format'}

${info.dependencies.length > 0 ? 
  'Requires: ' + info.dependencies.map(d => d.name).join(', ') : ''}

%files
${info.files.map(f => f.startsWith('/') ? f : '/' + f).join('\n')}
`;

    const specFile = path.join(specDir, `${info.name}.spec`);
    fs.writeFileSync(specFile, specContent);

    // Copy files to buildroot
    const contentDir = path.join(sourceDir, 'content');
    if (fs.existsSync(contentDir)) {
      execCommand(`cp -a "${contentDir}"/* "${buildRoot}/"`);
    }

    // Build RPM
    execCommand(`rpmbuild -bb --buildroot "${buildRoot}" "${specFile}" --define "_rpmdir ${path.dirname(outputPath)}"`);

    return outputPath;
  }

  async install(packagePath) {
    if (commandExists('dnf')) {
      execCommand(`sudo dnf install -y "${packagePath}"`);
    } else if (commandExists('yum')) {
      execCommand(`sudo yum install -y "${packagePath}"`);
    } else {
      execCommand(`sudo rpm -i "${packagePath}"`);
    }
  }

  async listInstalled() {
    const output = execCommand('rpm -qa --queryformat "%{NAME}|%{VERSION}|%{ARCH}\\n"', undefined, { throwOnError: false });
    if (!output) return [];

    return output.split('\n')
      .filter(Boolean)
      .map(line => {
        const [name, version, arch] = line.split('|');
        return { name, version, architecture: this.convertArch(arch) };
      });
  }

  async getInstalledInfo(packageName) {
    const output = execCommand(`rpm -qi "${packageName}"`, undefined, { throwOnError: false });
    if (!output) return null;

    const info = new PackageInfo({ sourceFormat: 'rpm' });
    
    for (const line of output.split('\n')) {
      const match = line.match(/^([^:]+):\s*(.*)$/);
      if (match) {
        const [, field, value] = match;
        switch (field.toLowerCase().trim()) {
          case 'name':
            info.name = value;
            break;
          case 'version':
            info.version = value;
            break;
          case 'architecture':
            info.architecture = this.convertArch(value);
            break;
          case 'summary':
            info.description = value;
            break;
        }
      }
    }

    return info;
  }
}

/**
 * Flatpak format handler
 */
class FlatpakHandler extends PackageFormatHandler {
  constructor() {
    super('flatpak');
  }

  isAvailable() {
    return commandExists('flatpak');
  }

  async extractInfo(packagePath) {
    const info = new PackageInfo({ sourceFormat: 'flatpak' });

    // Flatpak bundles (.flatpak files) can be inspected with flatpak info
    const output = execCommand(
      `flatpak info --show-metadata "${packagePath}"`,
      undefined,
      { throwOnError: false }
    );

    if (output) {
      const lines = output.split('\n');
      for (const line of lines) {
        if (line.startsWith('name=')) {
          info.name = line.split('=')[1];
        } else if (line.startsWith('version=')) {
          info.version = line.split('=')[1];
        }
      }
    }

    // Try to get more info from manifest if available
    const manifestOutput = execCommand(
      `flatpak info --show-permissions "${packagePath}"`,
      undefined,
      { throwOnError: false }
    );

    // Flatpak uses 'runtime' dependencies
    const runtimeOutput = execCommand(
      `flatpak info --show-runtime "${packagePath}"`,
      undefined,
      { throwOnError: false }
    );

    if (runtimeOutput) {
      info.dependencies = [{ name: runtimeOutput.trim(), version: null }];
    }

    return info;
  }

  async extractContents(packagePath, targetDir) {
    fs.mkdirSync(targetDir, { recursive: true });

    // Install flatpak to a temporary location and copy files
    // This is complex because flatpak uses OSTree
    const tempInstall = path.join(targetDir, '.flatpak-install');
    
    try {
      execCommand(
        `flatpak install --bundle --user --noninteractive "${packagePath}" --installation-path="${tempInstall}"`,
        undefined,
        { throwOnError: false }
      );

      // Copy the installed files
      const filesPath = path.join(tempInstall, 'app');
      if (fs.existsSync(filesPath)) {
        execCommand(`cp -a "${filesPath}"/* "${targetDir}/"`);
      }
    } catch (e) {
      // Fallback: just mark as flatpak
      fs.writeFileSync(path.join(targetDir, '.flatpak-source'), packagePath);
    }

    return targetDir;
  }

  async createPackage(sourceDir, info, outputPath) {
    // Create flatpak manifest
    const manifest = {
      'app-id': info.name.includes('.') ? info.name : `org.example.${info.name}`,
      runtime: 'org.freedesktop.Platform',
      'runtime-version': '23.08',
      sdk: 'org.freedesktop.Sdk',
      command: info.name,
      modules: [{
        name: info.name,
        buildsystem: 'simple',
        'build-commands': [
          'cp -r . /app/'
        ],
        sources: [{
          type: 'dir',
          path: sourceDir
        }]
      }]
    };

    const manifestPath = path.join(sourceDir, 'manifest.json');
    fs.writeFileSync(manifestPath, JSON.stringify(manifest, null, 2));

    // Build flatpak
    const buildDir = path.join(sourceDir, '.flatpak-build');
    const repoDir = path.join(sourceDir, '.flatpak-repo');

    execCommand(`flatpak-builder --force-clean "${buildDir}" "${manifestPath}"`);
    execCommand(`flatpak build-export "${repoDir}" "${buildDir}"`);
    execCommand(`flatpak build-bundle "${repoDir}" "${outputPath}" ${manifest['app-id']}`);

    return outputPath;
  }

  async install(packagePath) {
    execCommand(`flatpak install --bundle --user -y "${packagePath}"`);
  }

  async listInstalled() {
    const output = execCommand('flatpak list --app --columns=application,version,arch', undefined, { throwOnError: false });
    if (!output) return [];

    return output.split('\n')
      .slice(1) // Skip header
      .filter(Boolean)
      .map(line => {
        const [name, version, arch] = line.split('\t');
        return { name, version, architecture: arch };
      });
  }

  async getInstalledInfo(packageName) {
    const output = execCommand(`flatpak info ${packageName}`, undefined, { throwOnError: false });
    if (!output) return null;

    const info = new PackageInfo({ sourceFormat: 'flatpak' });
    info.name = packageName;

    for (const line of output.split('\n')) {
      const match = line.match(/^\s*(\w+):\s*(.+)$/);
      if (match) {
        const [, field, value] = match;
        switch (field.toLowerCase()) {
          case 'version':
            info.version = value;
            break;
          case 'arch':
            info.architecture = value;
            break;
        }
      }
    }

    return info;
  }
}

/**
 * Snap format handler
 */
class SnapHandler extends PackageFormatHandler {
  constructor() {
    super('snap');
  }

  isAvailable() {
    return commandExists('snap') && commandExists('unsquashfs');
  }

  async extractInfo(packagePath) {
    const info = new PackageInfo({ sourceFormat: 'snap' });

    // Snaps are squashfs images, extract snap.yaml
    const tempDir = fs.mkdtempSync('/tmp/snap-extract-');
    
    try {
      execCommand(`unsquashfs -d "${tempDir}/content" "${packagePath}" meta/snap.yaml 2>/dev/null`);
      
      const snapYamlPath = path.join(tempDir, 'content', 'meta', 'snap.yaml');
      if (fs.existsSync(snapYamlPath)) {
        const snapYaml = fs.readFileSync(snapYamlPath, 'utf-8');
        
        // Parse YAML manually (simple key: value format)
        for (const line of snapYaml.split('\n')) {
          const match = line.match(/^(\w+):\s*(.+)$/);
          if (match) {
            const [, key, value] = match;
            switch (key.toLowerCase()) {
              case 'name':
                info.name = value.trim();
                break;
              case 'version':
                info.version = value.trim();
                break;
              case 'summary':
              case 'description':
                info.description = value.trim();
                break;
              case 'architectures':
                info.architecture = value.trim();
                break;
            }
          }
        }
      }
    } finally {
      execCommand(`rm -rf "${tempDir}"`, undefined, { throwOnError: false });
    }

    return info;
  }

  async extractContents(packagePath, targetDir) {
    fs.mkdirSync(targetDir, { recursive: true });
    execCommand(`unsquashfs -d "${targetDir}" "${packagePath}" 2>/dev/null`);
    return targetDir;
  }

  async createPackage(sourceDir, info, outputPath) {
    // Create snapcraft.yaml
    const snapDir = path.join(sourceDir, 'snap');
    fs.mkdirSync(snapDir, { recursive: true });

    const snapcraft = `
name: ${info.name}
version: '${info.version}'
summary: ${info.description.split('\n')[0] || 'Converted package'}
description: |
  ${info.description || 'Package converted from another format'}

base: core22
confinement: strict

apps:
  ${info.name}:
    command: bin/${info.name}

parts:
  ${info.name}:
    plugin: dump
    source: .
`;

    fs.writeFileSync(path.join(snapDir, 'snapcraft.yaml'), snapcraft);

    // Build snap
    execCommand(`cd "${sourceDir}" && snapcraft --destructive-mode`);
    
    // Find and move the built snap
    const snaps = fs.readdirSync(sourceDir).filter(f => f.endsWith('.snap'));
    if (snaps.length > 0) {
      fs.renameSync(path.join(sourceDir, snaps[0]), outputPath);
    }

    return outputPath;
  }

  async install(packagePath) {
    execCommand(`sudo snap install --dangerous "${packagePath}"`);
  }

  async listInstalled() {
    const output = execCommand('snap list', undefined, { throwOnError: false });
    if (!output) return [];

    return output.split('\n')
      .slice(1) // Skip header
      .filter(Boolean)
      .map(line => {
        const parts = line.split(/\s+/);
        return {
          name: parts[0],
          version: parts[1],
          architecture: 'all'
        };
      });
  }

  async getInstalledInfo(packageName) {
    const output = execCommand(`snap info ${packageName}`, undefined, { throwOnError: false });
    if (!output) return null;

    const info = new PackageInfo({ sourceFormat: 'snap' });
    info.name = packageName;

    for (const line of output.split('\n')) {
      const match = line.match(/^(\w+):\s*(.+)$/);
      if (match) {
        const [, field, value] = match;
        switch (field.toLowerCase()) {
          case 'installed':
            info.version = value.split(/\s+/)[0];
            break;
          case 'summary':
            info.description = value;
            break;
        }
      }
    }

    return info;
  }
}

/**
 * Pacman format handler (Arch Linux)
 */
class PacmanHandler extends PackageFormatHandler {
  constructor() {
    super('pacman');
  }

  isAvailable() {
    return commandExists('pacman') || commandExists('bsdtar');
  }

  async extractInfo(packagePath) {
    const info = new PackageInfo({ sourceFormat: 'pacman' });

    // Pacman packages are tar.zst or tar.xz archives with .PKGINFO
    const tempDir = fs.mkdtempSync('/tmp/pacman-extract-');
    
    try {
      // Detect archive type and extract
      if (packagePath.endsWith('.zst')) {
        execCommand(`zstd -d -c "${packagePath}" | tar -xf - -C "${tempDir}" .PKGINFO 2>/dev/null || true`);
      } else {
        execCommand(`tar -xf "${packagePath}" -C "${tempDir}" .PKGINFO 2>/dev/null || true`);
      }
      
      const pkginfoPath = path.join(tempDir, '.PKGINFO');
      if (fs.existsSync(pkginfoPath)) {
        const pkginfo = fs.readFileSync(pkginfoPath, 'utf-8');
        
        for (const line of pkginfo.split('\n')) {
          const match = line.match(/^(\w+)\s*=\s*(.+)$/);
          if (match) {
            const [, key, value] = match;
            switch (key.toLowerCase()) {
              case 'pkgname':
                info.name = value.trim();
                break;
              case 'pkgver':
                info.version = value.trim();
                break;
              case 'pkgdesc':
                info.description = value.trim();
                break;
              case 'arch':
                info.architecture = this.convertArch(value.trim());
                break;
              case 'depend':
                info.dependencies.push({ name: value.trim(), version: null });
                break;
              case 'provides':
                info.provides.push(value.trim());
                break;
              case 'conflict':
                info.conflicts.push(value.trim());
                break;
              case 'url':
                info.homepage = value.trim();
                break;
              case 'license':
                info.license = value.trim();
                break;
              case 'size':
                info.size = parseInt(value.trim()) || 0;
                break;
            }
          }
        }
      }
    } finally {
      execCommand(`rm -rf "${tempDir}"`, undefined, { throwOnError: false });
    }

    return info;
  }

  convertArch(pacmanArch) {
    const archMap = {
      'x86_64': 'amd64',
      'i686': 'i386',
      'any': 'all',
      'aarch64': 'arm64'
    };
    return archMap[pacmanArch] || pacmanArch;
  }

  convertArchToPacman(debArch) {
    const archMap = {
      'amd64': 'x86_64',
      'i386': 'i686',
      'all': 'any',
      'arm64': 'aarch64'
    };
    return archMap[debArch] || debArch;
  }

  async extractContents(packagePath, targetDir) {
    fs.mkdirSync(targetDir, { recursive: true });
    
    if (packagePath.endsWith('.zst')) {
      execCommand(`zstd -d -c "${packagePath}" | tar -xf - -C "${targetDir}"`);
    } else {
      execCommand(`tar -xf "${packagePath}" -C "${targetDir}"`);
    }
    
    return targetDir;
  }

  async createPackage(sourceDir, info, outputPath) {
    // Create .PKGINFO
    const pkginfoContent = [
      `pkgname = ${info.name}`,
      `pkgver = ${info.version.replace(/-/g, '_')}`,
      `pkgdesc = ${info.description.split('\n')[0] || 'Converted package'}`,
      `arch = ${this.convertArchToPacman(info.architecture)}`,
      `size = ${info.size}`,
      `url = ${info.homepage || 'https://example.com'}`,
      `license = ${info.license || 'unknown'}`,
    ];

    for (const dep of info.dependencies) {
      pkginfoContent.push(`depend = ${dep.name}`);
    }

    for (const prov of info.provides) {
      pkginfoContent.push(`provides = ${prov}`);
    }

    for (const conf of info.conflicts) {
      pkginfoContent.push(`conflict = ${conf}`);
    }

    fs.writeFileSync(path.join(sourceDir, '.PKGINFO'), pkginfoContent.join('\n') + '\n');

    // Create the package
    const files = fs.readdirSync(sourceDir).filter(f => !f.startsWith('.'));
    const allFiles = ['.PKGINFO', ...files];

    if (outputPath.endsWith('.zst')) {
      execCommand(`cd "${sourceDir}" && tar -cf - ${allFiles.join(' ')} | zstd -o "${outputPath}"`);
    } else {
      execCommand(`cd "${sourceDir}" && tar -cJf "${outputPath}" ${allFiles.join(' ')}`);
    }

    return outputPath;
  }

  async install(packagePath) {
    execCommand(`sudo pacman -U --noconfirm "${packagePath}"`);
  }

  async listInstalled() {
    const output = execCommand('pacman -Q', undefined, { throwOnError: false });
    if (!output) return [];

    return output.split('\n')
      .filter(Boolean)
      .map(line => {
        const [name, version] = line.split(' ');
        return { name, version, architecture: 'all' };
      });
  }

  async getInstalledInfo(packageName) {
    const output = execCommand(`pacman -Qi ${packageName}`, undefined, { throwOnError: false });
    if (!output) return null;

    const info = new PackageInfo({ sourceFormat: 'pacman' });

    for (const line of output.split('\n')) {
      const match = line.match(/^([^:]+):\s*(.+)$/);
      if (match) {
        const [, field, value] = match;
        switch (field.toLowerCase().trim()) {
          case 'name':
            info.name = value;
            break;
          case 'version':
            info.version = value;
            break;
          case 'architecture':
            info.architecture = this.convertArch(value);
            break;
          case 'description':
            info.description = value;
            break;
        }
      }
    }

    return info;
  }
}

/**
 * Package Converter - Main conversion logic using .deb as hub
 */
class PackageConverter {
  constructor() {
    this.handlers = {
      deb: new DebHandler(),
      rpm: new RpmHandler(),
      flatpak: new FlatpakHandler(),
      snap: new SnapHandler(),
      pacman: new PacmanHandler()
    };
  }

  /**
   * Get available package formats on this system
   */
  getAvailableFormats() {
    return Object.entries(this.handlers)
      .filter(([, handler]) => handler.isAvailable())
      .map(([format]) => format);
  }

  /**
   * Detect format from file extension or content
   */
  detectFormat(packagePath) {
    const ext = path.extname(packagePath).toLowerCase();
    const basename = path.basename(packagePath).toLowerCase();

    if (ext === '.deb') return 'deb';
    if (ext === '.rpm') return 'rpm';
    if (ext === '.flatpak' || ext === '.flatpakref') return 'flatpak';
    if (ext === '.snap') return 'snap';
    if (basename.includes('.pkg.tar') || ext === '.zst' || ext === '.xz') return 'pacman';

    // Try to detect from content
    try {
      const header = execCommand(`file "${packagePath}"`, undefined, { throwOnError: false });
      if (header) {
        if (header.includes('Debian binary package')) return 'deb';
        if (header.includes('RPM')) return 'rpm';
        if (header.includes('Squashfs')) return 'snap';
      }
    } catch {
      // Ignore detection errors
    }

    return null;
  }

  /**
   * Convert a package from one format to another
   * Uses .deb as the hub format
   */
  async convert(sourcePath, targetFormat, outputPath = null) {
    const spinner = ora('Detecting source format...').start();

    try {
      // Detect source format
      const sourceFormat = this.detectFormat(sourcePath);
      if (!sourceFormat) {
        throw new Error(`Could not detect format of ${sourcePath}`);
      }

      spinner.text = `Source format: ${sourceFormat}`;

      if (sourceFormat === targetFormat) {
        spinner.succeed('Source and target formats are the same');
        return sourcePath;
      }

      // Validate handlers are available
      const sourceHandler = this.handlers[sourceFormat];
      const targetHandler = this.handlers[targetFormat];
      const debHandler = this.handlers.deb;

      if (!sourceHandler) {
        throw new Error(`Unsupported source format: ${sourceFormat}`);
      }
      if (!targetHandler) {
        throw new Error(`Unsupported target format: ${targetFormat}`);
      }

      // Create temp directory for conversion
      const tempDir = fs.mkdtempSync('/tmp/pkg-convert-');
      const contentDir = path.join(tempDir, 'content');
      
      try {
        // Step 1: Extract package info
        spinner.text = 'Extracting package information...';
        const info = await sourceHandler.extractInfo(sourcePath);
        
        // Step 2: Extract contents
        spinner.text = 'Extracting package contents...';
        await sourceHandler.extractContents(sourcePath, contentDir);

        // Step 3: Convert via .deb hub if needed
        let intermediateInfo = info;
        let intermediateDir = contentDir;

        if (sourceFormat !== 'deb' && targetFormat !== 'deb') {
          // Convert to .deb first
          spinner.text = `Converting ${sourceFormat} → deb (hub format)...`;
          const debPath = path.join(tempDir, `${info.name}_${info.version}.deb`);
          
          await debHandler.createPackage(contentDir, info, debPath);
          
          // Re-extract from .deb to ensure consistency
          intermediateDir = path.join(tempDir, 'deb-content');
          await debHandler.extractContents(debPath, intermediateDir);
          intermediateInfo = await debHandler.extractInfo(debPath);
        }

        // Step 4: Create target package
        spinner.text = `Creating ${targetFormat} package...`;
        
        const defaultOutputPath = outputPath || this.generateOutputPath(sourcePath, targetFormat, info);
        await targetHandler.createPackage(intermediateDir, intermediateInfo, defaultOutputPath);

        spinner.succeed(`Converted ${sourceFormat} → ${targetFormat}: ${defaultOutputPath}`);
        
        return defaultOutputPath;

      } finally {
        // Cleanup temp directory
        execCommand(`rm -rf "${tempDir}"`, undefined, { throwOnError: false });
      }

    } catch (error) {
      spinner.fail(`Conversion failed: ${error.message}`);
      throw error;
    }
  }

  /**
   * Generate output path based on package info and target format
   */
  generateOutputPath(sourcePath, targetFormat, info) {
    const dir = path.dirname(sourcePath);
    const name = info.name || path.basename(sourcePath, path.extname(sourcePath));
    const version = info.version || '1.0';
    const arch = info.architecture || 'all';

    switch (targetFormat) {
      case 'deb':
        return path.join(dir, `${name}_${version}_${arch}.deb`);
      case 'rpm':
        return path.join(dir, `${name}-${version}.${arch}.rpm`);
      case 'flatpak':
        return path.join(dir, `${name}-${version}.flatpak`);
      case 'snap':
        return path.join(dir, `${name}_${version}_${arch}.snap`);
      case 'pacman':
        return path.join(dir, `${name}-${version}-${arch}.pkg.tar.zst`);
      default:
        return path.join(dir, `${name}-${version}.${targetFormat}`);
    }
  }

  /**
   * Get package information
   */
  async getInfo(packagePath) {
    const format = this.detectFormat(packagePath);
    if (!format) {
      throw new Error(`Could not detect format of ${packagePath}`);
    }

    const handler = this.handlers[format];
    if (!handler) {
      throw new Error(`No handler for format: ${format}`);
    }

    return await handler.extractInfo(packagePath);
  }

  /**
   * Resolve dependencies across formats
   */
  async resolveDependencies(packagePath, targetFormat) {
    const info = await this.getInfo(packagePath);
    const targetHandler = this.handlers[targetFormat];

    if (!targetHandler) {
      throw new Error(`Unknown target format: ${targetFormat}`);
    }

    // Get list of installed packages in target format
    const installed = await targetHandler.listInstalled();
    const installedNames = new Set(installed.map(p => p.name));

    // Check which dependencies are missing
    const missing = [];
    const available = [];

    for (const dep of info.dependencies) {
      if (installedNames.has(dep.name)) {
        available.push(dep);
      } else {
        missing.push(dep);
      }
    }

    return {
      total: info.dependencies.length,
      available,
      missing,
      allSatisfied: missing.length === 0
    };
  }
}

/**
 * CLI Interface
 */
async function main() {
  const args = process.argv.slice(2);
  
  if (args.length === 0 || args.includes('--help') || args.includes('-h')) {
    printHelp();
    process.exit(0);
  }

  const converter = new PackageConverter();

  const command = args[0];

  switch (command) {
    case 'convert': {
      if (args.length < 3) {
        console.error(chalk.red('Usage: package-manager convert <source-package> <target-format> [output-path]'));
        process.exit(1);
      }
      
      const [, sourcePath, targetFormat, outputPath] = args;
      
      if (!SUPPORTED_FORMATS.includes(targetFormat)) {
        console.error(chalk.red(`Unsupported target format: ${targetFormat}`));
        console.log(chalk.yellow(`Supported formats: ${SUPPORTED_FORMATS.join(', ')}`));
        process.exit(1);
      }

      try {
        const result = await converter.convert(sourcePath, targetFormat, outputPath);
        console.log(chalk.green(`\n✓ Package converted successfully: ${result}`));
      } catch (error) {
        console.error(chalk.red(`\n✗ Conversion failed: ${error.message}`));
        process.exit(1);
      }
      break;
    }

    case 'info': {
      if (args.length < 2) {
        console.error(chalk.red('Usage: package-manager info <package-path>'));
        process.exit(1);
      }

      try {
        const info = await converter.getInfo(args[1]);
        console.log(chalk.bold('\nPackage Information:\n'));
        console.log(chalk.cyan('Name:        ') + info.name);
        console.log(chalk.cyan('Version:     ') + info.version);
        console.log(chalk.cyan('Architecture:') + info.architecture);
        console.log(chalk.cyan('Description: ') + info.description);
        console.log(chalk.cyan('Format:      ') + info.sourceFormat);
        
        if (info.dependencies.length > 0) {
          console.log(chalk.cyan('\nDependencies:'));
          for (const dep of info.dependencies) {
            console.log(`  - ${dep.name}${dep.version ? ` (${dep.version})` : ''}`);
          }
        }

        if (info.files.length > 0) {
          console.log(chalk.cyan(`\nFiles: (${info.files.length} total)`));
          for (const file of info.files.slice(0, 10)) {
            console.log(`  ${file}`);
          }
          if (info.files.length > 10) {
            console.log(chalk.gray(`  ... and ${info.files.length - 10} more`));
          }
        }
      } catch (error) {
        console.error(chalk.red(`\n✗ Failed to get info: ${error.message}`));
        process.exit(1);
      }
      break;
    }

    case 'deps': {
      if (args.length < 3) {
        console.error(chalk.red('Usage: package-manager deps <package-path> <target-format>'));
        process.exit(1);
      }

      try {
        const deps = await converter.resolveDependencies(args[1], args[2]);
        console.log(chalk.bold('\nDependency Resolution:\n'));
        console.log(chalk.cyan('Total dependencies: ') + deps.total);
        console.log(chalk.green('Available:          ') + deps.available.length);
        console.log(chalk.yellow('Missing:            ') + deps.missing.length);
        
        if (deps.missing.length > 0) {
          console.log(chalk.yellow('\nMissing dependencies:'));
          for (const dep of deps.missing) {
            console.log(`  - ${dep.name}${dep.version ? ` (${dep.version})` : ''}`);
          }
        }

        console.log(deps.allSatisfied ? 
          chalk.green('\n✓ All dependencies satisfied') :
          chalk.yellow('\n⚠ Some dependencies are missing')
        );
      } catch (error) {
        console.error(chalk.red(`\n✗ Failed to resolve dependencies: ${error.message}`));
        process.exit(1);
      }
      break;
    }

    case 'formats': {
      const available = converter.getAvailableFormats();
      console.log(chalk.bold('\nPackage Format Support:\n'));
      
      for (const format of SUPPORTED_FORMATS) {
        const status = available.includes(format) ? 
          chalk.green('✓ Available') : 
          chalk.red('✗ Not available');
        console.log(`  ${format.padEnd(10)} ${status}`);
      }
      
      console.log(chalk.gray('\nInstall missing tools to enable more formats.'));
      break;
    }

    case 'matrix': {
      console.log(chalk.bold('\nConversion Matrix:\n'));
      console.log(chalk.gray('All conversions use .deb as the hub format.\n'));
      
      const header = '        ' + SUPPORTED_FORMATS.map(f => f.padEnd(8)).join(' ');
      console.log(chalk.cyan(header));
      console.log('        ' + '-'.repeat(SUPPORTED_FORMATS.length * 9));
      
      for (const from of SUPPORTED_FORMATS) {
        let row = chalk.cyan(from.padEnd(8));
        for (const to of SUPPORTED_FORMATS) {
          if (from === to) {
            row += chalk.gray('   -    ');
          } else if (from === 'deb' || to === 'deb') {
            row += chalk.green('   ✓    ');
          } else {
            row += chalk.yellow(' ✓→deb  ');
          }
        }
        console.log(row);
      }
      
      console.log(chalk.gray('\nLegend: ✓ = direct, ✓→deb = via .deb hub'));
      break;
    }

    default:
      console.error(chalk.red(`Unknown command: ${command}`));
      printHelp();
      process.exit(1);
  }
}

function printHelp() {
  console.log(`
${chalk.bold('Package Manager Translation Tool')}

${chalk.cyan('Usage:')}
  package-manager <command> [options]

${chalk.cyan('Commands:')}
  convert <source> <target-format> [output]
    Convert a package from one format to another
    Uses .deb as hub format for cross-format conversion

  info <package>
    Display information about a package file

  deps <package> <target-format>
    Resolve dependencies for target format

  formats
    Show available package formats on this system

  matrix
    Show conversion compatibility matrix

${chalk.cyan('Supported Formats:')}
  deb       Debian/Ubuntu (.deb)
  rpm       Red Hat/Fedora/SUSE (.rpm)
  flatpak   Flatpak sandboxed apps (.flatpak)
  snap      Snap packages (.snap)
  pacman    Arch Linux (.pkg.tar.zst)

${chalk.cyan('Examples:')}
  # Convert RPM to DEB
  package-manager convert package.rpm deb

  # Convert Flatpak to RPM (via .deb hub)
  package-manager convert app.flatpak rpm

  # Get package info
  package-manager info package.deb

  # Check dependencies
  package-manager deps package.rpm deb

${chalk.cyan('Note:')}
  All cross-format conversions go through .deb as the hub format.
  Example: flatpak → deb → rpm
`);
}

// Run if executed directly
const isMainModule = import.meta.url === `file://${process.argv[1]}` || 
                     import.meta.url.endsWith(process.argv[1]) ||
                     process.argv[1]?.endsWith('package-manager.mjs');

if (isMainModule) {
  main().catch(error => {
    console.error(chalk.red(`\nFatal error: ${error.message}`));
    process.exit(1);
  });
}

export {
  PackageConverter,
  PackageInfo,
  PackageFormatHandler,
  DebHandler,
  RpmHandler,
  FlatpakHandler,
  SnapHandler,
  PacmanHandler,
  SUPPORTED_FORMATS
};
