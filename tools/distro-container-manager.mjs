#!/usr/bin/env node
/**
 * Distro Container Manager
 * 
 * Container-based approach to multi-distro package management:
 * - Uses lightweight containers for CentOS, Fedora, Arch, openSUSE
 * - Mounts volumes with rshared for artifact extraction
 * - Supports unified view or distro-specific path switching
 * - Manages container lifecycle efficiently (spin up, install, extract, tear down)
 */

import { spawn, execSync, spawnSync } from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import chalk from 'chalk';
import ora from 'ora';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Configuration
const CONFIG = {
  // Base directory for distro artifacts
  artifactBase: process.env.PF_DISTRO_ARTIFACTS || path.join(process.env.HOME, '.pf/distros'),
  
  // Container runtime (podman preferred, docker fallback)
  runtime: process.env.CONTAINER_RT || 'podman',
  
  // Supported distributions
  distros: {
    fedora: {
      image: 'localhost/pf-distro-fedora:latest',
      dockerfile: 'Dockerfile.distro-fedora',
      packageManager: 'dnf',
      description: 'Fedora Linux (DNF)'
    },
    centos: {
      image: 'localhost/pf-distro-centos:latest',
      dockerfile: 'Dockerfile.distro-centos',
      packageManager: 'dnf',
      description: 'CentOS/AlmaLinux (DNF/YUM)'
    },
    arch: {
      image: 'localhost/pf-distro-arch:latest',
      dockerfile: 'Dockerfile.distro-arch',
      packageManager: 'pacman',
      description: 'Arch Linux (Pacman)'
    },
    opensuse: {
      image: 'localhost/pf-distro-opensuse:latest',
      dockerfile: 'Dockerfile.distro-opensuse',
      packageManager: 'zypper',
      description: 'openSUSE (Zypper)'
    }
  },
  
  // View modes
  viewModes: ['unified', 'isolated']
};

/**
 * Execute a command and return result
 */
function execCommand(cmd, options = {}) {
  try {
    return execSync(cmd, {
      encoding: 'utf-8',
      maxBuffer: 50 * 1024 * 1024,
      ...options
    }).trim();
  } catch (error) {
    if (options.throwOnError !== false) {
      throw error;
    }
    return null;
  }
}

/**
 * Check if container runtime is available
 */
function getContainerRuntime() {
  let runtime = CONFIG.runtime;
  
  try {
    execSync(`which ${runtime}`, { stdio: 'pipe' });
    return runtime;
  } catch {
    // Fallback to docker
    try {
      execSync('which docker', { stdio: 'pipe' });
      return 'docker';
    } catch {
      throw new Error('Neither podman nor docker is available. Please install one.');
    }
  }
}

/**
 * Initialize artifact directories
 */
function initArtifactDirs() {
  const baseDir = CONFIG.artifactBase;
  
  // Create base directory
  fs.mkdirSync(baseDir, { recursive: true });
  
  // Create distro-specific directories
  for (const distro of Object.keys(CONFIG.distros)) {
    const distroDir = path.join(baseDir, distro);
    fs.mkdirSync(path.join(distroDir, 'bin'), { recursive: true });
    fs.mkdirSync(path.join(distroDir, 'lib'), { recursive: true });
    fs.mkdirSync(path.join(distroDir, 'share'), { recursive: true });
    fs.mkdirSync(path.join(distroDir, 'etc'), { recursive: true });
  }
  
  // Create unified directory with symlinks
  const unifiedDir = path.join(baseDir, 'unified');
  fs.mkdirSync(path.join(unifiedDir, 'bin'), { recursive: true });
  fs.mkdirSync(path.join(unifiedDir, 'lib'), { recursive: true });
  fs.mkdirSync(path.join(unifiedDir, 'share'), { recursive: true });
  
  // Create config file
  const configPath = path.join(baseDir, 'config.json');
  if (!fs.existsSync(configPath)) {
    fs.writeFileSync(configPath, JSON.stringify({
      activeDistro: null,
      viewMode: 'unified',
      installedPackages: {}
    }, null, 2));
  }
  
  return baseDir;
}

/**
 * Get current configuration
 */
function getConfig() {
  const configPath = path.join(CONFIG.artifactBase, 'config.json');
  if (fs.existsSync(configPath)) {
    return JSON.parse(fs.readFileSync(configPath, 'utf-8'));
  }
  return {
    activeDistro: null,
    viewMode: 'unified',
    installedPackages: {}
  };
}

/**
 * Save configuration
 */
function saveConfig(config) {
  const configPath = path.join(CONFIG.artifactBase, 'config.json');
  fs.writeFileSync(configPath, JSON.stringify(config, null, 2));
}

/**
 * Build distro container image
 */
async function buildDistroImage(distro) {
  const spinner = ora(`Building ${distro} container image...`).start();
  
  const runtime = getContainerRuntime();
  const distroConfig = CONFIG.distros[distro];
  
  if (!distroConfig) {
    spinner.fail(`Unknown distro: ${distro}`);
    throw new Error(`Unknown distro: ${distro}`);
  }
  
  const projectRoot = path.resolve(__dirname, '..');
  const dockerfile = path.join(projectRoot, 'containers/dockerfiles', distroConfig.dockerfile);
  
  try {
    execCommand(`${runtime} build -t ${distroConfig.image} -f ${dockerfile} ${projectRoot}`, {
      stdio: 'pipe'
    });
    spinner.succeed(`Built ${distro} container image`);
    return true;
  } catch (error) {
    spinner.fail(`Failed to build ${distro} image`);
    throw error;
  }
}

/**
 * Check if distro image exists
 */
function imageExists(distro) {
  const runtime = getContainerRuntime();
  const image = CONFIG.distros[distro]?.image;
  
  if (!image) return false;
  
  try {
    execCommand(`${runtime} image exists ${image}`, { stdio: 'pipe' });
    return true;
  } catch {
    return false;
  }
}

/**
 * Install package in distro container
 */
async function installPackage(distro, packages) {
  const spinner = ora(`Installing packages in ${distro} container...`).start();
  
  const runtime = getContainerRuntime();
  const distroConfig = CONFIG.distros[distro];
  
  if (!distroConfig) {
    spinner.fail(`Unknown distro: ${distro}`);
    throw new Error(`Unknown distro: ${distro}`);
  }
  
  // Ensure image exists
  if (!imageExists(distro)) {
    spinner.text = `Building ${distro} image first...`;
    await buildDistroImage(distro);
  }
  
  // Initialize directories
  initArtifactDirs();
  
  const outputDir = path.join(CONFIG.artifactBase, distro);
  const pkgList = Array.isArray(packages) ? packages.join(' ') : packages;
  
  spinner.text = `Installing ${pkgList} in ${distro}...`;
  
  try {
    // Run container with rshared mount for output
    const containerCmd = [
      runtime, 'run', '--rm',
      '-v', `${outputDir}:/output:rshared`,
      '--security-opt', 'label=disable',
      distroConfig.image,
      '/usr/local/bin/distro-extract',
      ...packages.split(/\s+/)
    ].join(' ');
    
    const result = execCommand(containerCmd, { throwOnError: false });
    
    if (result === null) {
      spinner.fail(`Failed to install packages in ${distro}`);
      return false;
    }
    
    // Update config with installed packages
    const config = getConfig();
    if (!config.installedPackages[distro]) {
      config.installedPackages[distro] = [];
    }
    for (const pkg of packages.split(/\s+/)) {
      if (!config.installedPackages[distro].includes(pkg)) {
        config.installedPackages[distro].push(pkg);
      }
    }
    saveConfig(config);
    
    // Update unified view if enabled
    if (config.viewMode === 'unified') {
      await updateUnifiedView();
    }
    
    spinner.succeed(`Installed ${pkgList} from ${distro}`);
    console.log(chalk.gray(`  Artifacts in: ${outputDir}`));
    
    return true;
  } catch (error) {
    spinner.fail(`Installation failed: ${error.message}`);
    throw error;
  }
}

/**
 * Update unified view with symlinks from all distros
 */
async function updateUnifiedView() {
  const unifiedDir = path.join(CONFIG.artifactBase, 'unified');
  
  // Clear existing symlinks in unified bin
  const unifiedBin = path.join(unifiedDir, 'bin');
  if (fs.existsSync(unifiedBin)) {
    for (const file of fs.readdirSync(unifiedBin)) {
      const filePath = path.join(unifiedBin, file);
      const stat = fs.lstatSync(filePath);
      if (stat.isSymbolicLink()) {
        fs.unlinkSync(filePath);
      }
    }
  }
  
  // Create symlinks from each distro
  for (const distro of Object.keys(CONFIG.distros)) {
    const distroBin = path.join(CONFIG.artifactBase, distro, 'bin');
    if (fs.existsSync(distroBin)) {
      for (const file of fs.readdirSync(distroBin)) {
        const source = path.join(distroBin, file);
        const target = path.join(unifiedBin, file);
        
        // Skip if already exists (first distro wins in unified mode)
        if (!fs.existsSync(target)) {
          try {
            fs.symlinkSync(source, target);
          } catch {
            // Ignore symlink errors
          }
        }
      }
    }
  }
}

/**
 * Switch active distro for PATH
 */
function switchDistro(distro) {
  const config = getConfig();
  
  if (distro && !CONFIG.distros[distro]) {
    throw new Error(`Unknown distro: ${distro}. Available: ${Object.keys(CONFIG.distros).join(', ')}`);
  }
  
  config.activeDistro = distro;
  saveConfig(config);
  
  // Print PATH modification instructions
  const artifactDir = distro 
    ? path.join(CONFIG.artifactBase, distro, 'bin')
    : path.join(CONFIG.artifactBase, 'unified', 'bin');
  
  console.log(chalk.bold('\nTo use this distro, add to your PATH:'));
  console.log(chalk.cyan(`  export PATH="${artifactDir}:$PATH"`));
  console.log('');
  console.log(chalk.gray('Or add to your shell profile for persistence.'));
  
  return artifactDir;
}

/**
 * Set view mode (unified or isolated)
 */
function setViewMode(mode) {
  if (!CONFIG.viewModes.includes(mode)) {
    throw new Error(`Invalid view mode: ${mode}. Use: ${CONFIG.viewModes.join(', ')}`);
  }
  
  const config = getConfig();
  config.viewMode = mode;
  saveConfig(config);
  
  if (mode === 'unified') {
    updateUnifiedView();
    console.log(chalk.green('✓ Switched to unified view'));
    console.log(chalk.gray('  Binaries from all distros available at:'));
    console.log(chalk.cyan(`  ${path.join(CONFIG.artifactBase, 'unified', 'bin')}`));
  } else {
    console.log(chalk.green('✓ Switched to isolated view'));
    console.log(chalk.gray('  Use "pf distro-switch <distro>" to select active distro'));
  }
}

/**
 * List installed packages and status
 */
function listStatus() {
  const config = getConfig();
  
  console.log(chalk.bold('\nDistro Container Manager Status\n'));
  console.log(chalk.cyan('View Mode:    ') + config.viewMode);
  console.log(chalk.cyan('Active Distro:') + (config.activeDistro || 'unified'));
  console.log(chalk.cyan('Artifact Dir: ') + CONFIG.artifactBase);
  console.log('');
  
  console.log(chalk.bold('Available Distros:'));
  console.log('');
  
  for (const [name, distro] of Object.entries(CONFIG.distros)) {
    const hasImage = imageExists(name);
    const packages = config.installedPackages[name] || [];
    const status = hasImage ? chalk.green('✓ Ready') : chalk.yellow('○ Not built');
    
    console.log(`  ${chalk.bold(name.padEnd(10))} ${status}`);
    console.log(`    ${chalk.gray(distro.description)}`);
    console.log(`    ${chalk.gray(`Package Manager: ${distro.packageManager}`)}`);
    
    if (packages.length > 0) {
      console.log(`    ${chalk.gray(`Installed: ${packages.join(', ')}`)}`);
    }
    console.log('');
  }
  
  // Show PATH setup
  const pathDir = config.viewMode === 'unified'
    ? path.join(CONFIG.artifactBase, 'unified', 'bin')
    : config.activeDistro
      ? path.join(CONFIG.artifactBase, config.activeDistro, 'bin')
      : null;
  
  if (pathDir) {
    console.log(chalk.bold('PATH Setup:'));
    console.log(chalk.cyan(`  export PATH="${pathDir}:$PATH"`));
    console.log('');
  }
}

/**
 * Build all distro images
 */
async function buildAllImages() {
  console.log(chalk.bold('\nBuilding all distro container images...\n'));
  
  for (const distro of Object.keys(CONFIG.distros)) {
    try {
      await buildDistroImage(distro);
    } catch (error) {
      console.error(chalk.red(`  Failed to build ${distro}: ${error.message}`));
    }
  }
  
  console.log(chalk.green('\n✓ Build complete'));
}

/**
 * Clean up containers and optionally artifacts
 */
function cleanup(removeArtifacts = false) {
  const runtime = getContainerRuntime();
  
  console.log(chalk.bold('\nCleaning up distro containers...\n'));
  
  // Remove container images
  for (const [name, distro] of Object.entries(CONFIG.distros)) {
    try {
      execCommand(`${runtime} rmi ${distro.image}`, { throwOnError: false, stdio: 'pipe' });
      console.log(chalk.green(`  ✓ Removed ${name} image`));
    } catch {
      console.log(chalk.gray(`  - ${name} image not found`));
    }
  }
  
  if (removeArtifacts) {
    console.log('');
    console.log(chalk.yellow('  Removing artifact directories...'));
    try {
      fs.rmSync(CONFIG.artifactBase, { recursive: true, force: true });
      console.log(chalk.green(`  ✓ Removed ${CONFIG.artifactBase}`));
    } catch (error) {
      console.error(chalk.red(`  ✗ Failed to remove artifacts: ${error.message}`));
    }
  }
  
  console.log(chalk.green('\n✓ Cleanup complete'));
}

/**
 * Print help
 */
function printHelp() {
  console.log(`
${chalk.bold('Distro Container Manager')}

${chalk.cyan('Usage:')}
  node tools/distro-container-manager.mjs <command> [options]

${chalk.cyan('Commands:')}
  ${chalk.bold('install')} <distro> <packages>
    Install packages from a specific distro container
    Example: install fedora vim htop

  ${chalk.bold('switch')} <distro>
    Switch active distro for PATH (isolated mode)
    Example: switch fedora

  ${chalk.bold('view')} <mode>
    Set view mode: unified or isolated
    - unified: all distro binaries in one directory
    - isolated: separate directories per distro

  ${chalk.bold('build')} [distro]
    Build distro container image(s)
    - No argument: build all
    - With distro: build specific one

  ${chalk.bold('status')}
    Show status of all distros and installed packages

  ${chalk.bold('cleanup')} [--artifacts]
    Remove container images
    --artifacts: also remove extracted files

  ${chalk.bold('init')}
    Initialize artifact directories

${chalk.cyan('Supported Distros:')}
  fedora    - Fedora Linux (DNF)
  centos    - CentOS/AlmaLinux (DNF/YUM)
  arch      - Arch Linux (Pacman)
  opensuse  - openSUSE (Zypper)

${chalk.cyan('Environment Variables:')}
  PF_DISTRO_ARTIFACTS  Base directory for artifacts (default: ~/.pf/distros)
  CONTAINER_RT         Container runtime (default: podman)

${chalk.cyan('Technical Details:')}
  - Uses rshared bind mounts for efficient artifact extraction
  - Each distro has isolated /bin, /lib, /share, /etc directories
  - Unified view creates symlinks from all distros to one location

${chalk.cyan('Examples:')}
  # Install htop from Fedora
  node tools/distro-container-manager.mjs install fedora htop

  # Install multiple packages from Arch
  node tools/distro-container-manager.mjs install arch "vim neovim tree"

  # Switch to unified view
  node tools/distro-container-manager.mjs view unified

  # Check status
  node tools/distro-container-manager.mjs status
`);
}

// CLI handling
async function main() {
  const args = process.argv.slice(2);
  const command = args[0];
  
  if (!command || command === '--help' || command === '-h') {
    printHelp();
    process.exit(0);
  }
  
  try {
    switch (command) {
      case 'install': {
        const distro = args[1];
        const packages = args.slice(2).join(' ');
        
        if (!distro || !packages) {
          console.error(chalk.red('Usage: install <distro> <packages>'));
          process.exit(1);
        }
        
        await installPackage(distro, packages);
        break;
      }
      
      case 'switch': {
        const distro = args[1];
        switchDistro(distro || null);
        break;
      }
      
      case 'view': {
        const mode = args[1];
        if (!mode) {
          console.error(chalk.red('Usage: view <unified|isolated>'));
          process.exit(1);
        }
        setViewMode(mode);
        break;
      }
      
      case 'build': {
        const distro = args[1];
        if (distro) {
          await buildDistroImage(distro);
        } else {
          await buildAllImages();
        }
        break;
      }
      
      case 'status': {
        initArtifactDirs();
        listStatus();
        break;
      }
      
      case 'cleanup': {
        const removeArtifacts = args.includes('--artifacts');
        cleanup(removeArtifacts);
        break;
      }
      
      case 'init': {
        initArtifactDirs();
        console.log(chalk.green(`✓ Initialized artifact directories at ${CONFIG.artifactBase}`));
        break;
      }
      
      default:
        console.error(chalk.red(`Unknown command: ${command}`));
        printHelp();
        process.exit(1);
    }
  } catch (error) {
    console.error(chalk.red(`Error: ${error.message}`));
    process.exit(1);
  }
}

// Run CLI
const isMainModule = import.meta.url === `file://${process.argv[1]}` || 
                     import.meta.url.endsWith(process.argv[1]) ||
                     process.argv[1]?.endsWith('distro-container-manager.mjs');

if (isMainModule) {
  main();
}

export {
  CONFIG,
  initArtifactDirs,
  buildDistroImage,
  installPackage,
  switchDistro,
  setViewMode,
  listStatus,
  cleanup,
  getContainerRuntime
};
