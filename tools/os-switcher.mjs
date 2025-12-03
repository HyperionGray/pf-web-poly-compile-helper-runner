#!/usr/bin/env node
/**
 * OS Switcher (pf switch-os)
 * 
 * Advanced OS switching using containers and kexec:
 * - MirrorOS: Continuous snapshots of base OS via rsync/zfs/btrfs
 * - Container expansion with device mounting
 * - Safe backup procedures before switch
 * - Rebootless kernel switching via kexec
 * 
 * CAUTION: This is a powerful system-level tool that can modify your OS.
 * Use with extreme care and always have backups.
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
  // Base directory for OS switching operations
  switchBase: process.env.PF_SWITCH_BASE || path.join(process.env.HOME, '.pf/os-switch'),
  
  // Container runtime
  runtime: process.env.CONTAINER_RT || 'podman',
  
  // Supported target OS containers
  targetOS: {
    fedora: {
      image: 'docker.io/library/fedora:40',
      kernel: '/boot/vmlinuz',
      initrd: '/boot/initramfs.img'
    },
    arch: {
      image: 'docker.io/library/archlinux:latest',
      kernel: '/boot/vmlinuz-linux',
      initrd: '/boot/initramfs-linux.img'
    },
    ubuntu: {
      image: 'docker.io/library/ubuntu:24.04',
      kernel: '/boot/vmlinuz',
      initrd: '/boot/initrd.img'
    },
    debian: {
      image: 'docker.io/library/debian:bookworm',
      kernel: '/boot/vmlinuz',
      initrd: '/boot/initrd.img'
    }
  },
  
  // Snapshot methods in order of preference
  snapshotMethods: ['btrfs', 'zfs', 'rsync']
};

/**
 * Execute command with error handling
 */
function execCommand(cmd, options = {}) {
  try {
    return execSync(cmd, {
      encoding: 'utf-8',
      maxBuffer: 100 * 1024 * 1024,
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
 * Check if running as root
 */
function checkRoot() {
  if (process.getuid && process.getuid() !== 0) {
    console.error(chalk.red('ERROR: This operation requires root privileges.'));
    console.error(chalk.yellow('Please run with: sudo pf switch-os ...'));
    process.exit(1);
  }
}

/**
 * Detect available snapshot method
 */
function detectSnapshotMethod() {
  // Check for btrfs
  try {
    const fsType = execCommand('stat -f -c %T /', { throwOnError: false });
    if (fsType === 'btrfs') {
      return 'btrfs';
    }
  } catch {}
  
  // Check for zfs
  try {
    execCommand('which zfs', { throwOnError: false, stdio: 'pipe' });
    const zpools = execCommand('zpool list -H', { throwOnError: false });
    if (zpools) {
      return 'zfs';
    }
  } catch {}
  
  // Fallback to rsync
  try {
    execCommand('which rsync', { throwOnError: false, stdio: 'pipe' });
    return 'rsync';
  } catch {}
  
  return null;
}

/**
 * Get container runtime
 */
function getContainerRuntime() {
  let runtime = CONFIG.runtime;
  
  try {
    execSync(`which ${runtime}`, { stdio: 'pipe' });
    return runtime;
  } catch {
    try {
      execSync('which docker', { stdio: 'pipe' });
      return 'docker';
    } catch {
      throw new Error('Neither podman nor docker is available.');
    }
  }
}

/**
 * Initialize switch directories
 */
function initSwitchDirs() {
  const dirs = [
    CONFIG.switchBase,
    path.join(CONFIG.switchBase, 'snapshots'),
    path.join(CONFIG.switchBase, 'backups'),
    path.join(CONFIG.switchBase, 'staging'),
    path.join(CONFIG.switchBase, 'logs')
  ];
  
  for (const dir of dirs) {
    fs.mkdirSync(dir, { recursive: true });
  }
  
  return CONFIG.switchBase;
}

/**
 * MirrorOS: Create snapshot of current OS
 */
async function createSnapshot(name = null) {
  const spinner = ora('Creating OS snapshot...').start();
  
  const method = detectSnapshotMethod();
  if (!method) {
    spinner.fail('No snapshot method available (need btrfs, zfs, or rsync)');
    return null;
  }
  
  const snapshotName = name || `snapshot-${Date.now()}`;
  const snapshotDir = path.join(CONFIG.switchBase, 'snapshots', snapshotName);
  
  spinner.text = `Creating snapshot using ${method}...`;
  
  try {
    switch (method) {
      case 'btrfs': {
        // Create btrfs snapshot
        const subvol = execCommand('btrfs subvolume show /', { throwOnError: false });
        if (subvol) {
          execCommand(`btrfs subvolume snapshot / ${snapshotDir}`);
        } else {
          // Fallback to rsync for non-subvolume root
          fs.mkdirSync(snapshotDir, { recursive: true });
          execCommand(`rsync -axHAWXS --numeric-ids --info=progress2 / ${snapshotDir}/ --exclude=/proc --exclude=/sys --exclude=/dev --exclude=/run --exclude=/tmp --exclude="${CONFIG.switchBase}"`);
        }
        break;
      }
      
      case 'zfs': {
        // Create zfs snapshot
        const dataset = execCommand('zfs list -H -o name /', { throwOnError: false });
        if (dataset) {
          execCommand(`zfs snapshot ${dataset}@${snapshotName}`);
        } else {
          spinner.fail('Could not determine ZFS dataset');
          return null;
        }
        break;
      }
      
      case 'rsync': {
        // rsync backup
        fs.mkdirSync(snapshotDir, { recursive: true });
        execCommand(`rsync -axHAWXS --numeric-ids / ${snapshotDir}/ --exclude=/proc --exclude=/sys --exclude=/dev --exclude=/run --exclude=/tmp --exclude="${CONFIG.switchBase}"`, {
          stdio: 'inherit'
        });
        break;
      }
    }
    
    // Save snapshot metadata
    const metadata = {
      name: snapshotName,
      method,
      timestamp: new Date().toISOString(),
      kernel: execCommand('uname -r', { throwOnError: false }),
      hostname: execCommand('hostname', { throwOnError: false })
    };
    
    fs.writeFileSync(
      path.join(CONFIG.switchBase, 'snapshots', `${snapshotName}.json`),
      JSON.stringify(metadata, null, 2)
    );
    
    spinner.succeed(`Created snapshot: ${snapshotName} (${method})`);
    return { name: snapshotName, method, dir: snapshotDir };
  } catch (error) {
    spinner.fail(`Snapshot failed: ${error.message}`);
    throw error;
  }
}

/**
 * List available snapshots
 */
function listSnapshots() {
  const snapshotsDir = path.join(CONFIG.switchBase, 'snapshots');
  
  if (!fs.existsSync(snapshotsDir)) {
    console.log(chalk.yellow('No snapshots found.'));
    return [];
  }
  
  const snapshots = [];
  const files = fs.readdirSync(snapshotsDir);
  
  for (const file of files) {
    if (file.endsWith('.json')) {
      try {
        const metadata = JSON.parse(
          fs.readFileSync(path.join(snapshotsDir, file), 'utf-8')
        );
        snapshots.push(metadata);
      } catch {}
    }
  }
  
  if (snapshots.length === 0) {
    console.log(chalk.yellow('No snapshots found.'));
  } else {
    console.log(chalk.bold('\nAvailable Snapshots:\n'));
    for (const snap of snapshots) {
      console.log(`  ${chalk.cyan(snap.name)}`);
      console.log(`    Method: ${snap.method}`);
      console.log(`    Date:   ${snap.timestamp}`);
      console.log(`    Kernel: ${snap.kernel}`);
      console.log('');
    }
  }
  
  return snapshots;
}

/**
 * Prepare target OS container
 */
async function prepareTargetOS(targetOS, targetPartition) {
  const spinner = ora(`Preparing ${targetOS} container...`).start();
  
  const runtime = getContainerRuntime();
  const osConfig = CONFIG.targetOS[targetOS];
  
  if (!osConfig) {
    spinner.fail(`Unknown target OS: ${targetOS}`);
    throw new Error(`Unknown target OS: ${targetOS}`);
  }
  
  try {
    // Pull the image
    spinner.text = `Pulling ${targetOS} image...`;
    execCommand(`${runtime} pull ${osConfig.image}`, { stdio: 'pipe' });
    
    // Create staging area
    const stagingDir = path.join(CONFIG.switchBase, 'staging', targetOS);
    fs.mkdirSync(stagingDir, { recursive: true });
    
    // Export container filesystem
    spinner.text = `Exporting ${targetOS} filesystem...`;
    const containerId = execCommand(
      `${runtime} create ${osConfig.image} /bin/true`,
      { throwOnError: false }
    );
    
    if (containerId) {
      execCommand(`${runtime} export ${containerId} | tar -xf - -C ${stagingDir}`);
      execCommand(`${runtime} rm ${containerId}`, { throwOnError: false, stdio: 'pipe' });
    }
    
    spinner.succeed(`Prepared ${targetOS} in ${stagingDir}`);
    return { stagingDir, osConfig };
  } catch (error) {
    spinner.fail(`Failed to prepare ${targetOS}: ${error.message}`);
    throw error;
  }
}

/**
 * Check for kexec support
 */
function checkKexecSupport() {
  try {
    execCommand('which kexec', { throwOnError: false, stdio: 'pipe' });
    return true;
  } catch {
    return false;
  }
}

/**
 * Perform kexec to new kernel
 */
async function performKexec(kernelPath, initrdPath, cmdline = null) {
  const spinner = ora('Preparing kexec...').start();
  
  if (!checkKexecSupport()) {
    spinner.fail('kexec-tools not installed. Install with: apt install kexec-tools');
    return false;
  }
  
  // Get current kernel cmdline if not specified
  if (!cmdline) {
    cmdline = fs.readFileSync('/proc/cmdline', 'utf-8').trim();
  }
  
  try {
    spinner.text = 'Loading new kernel...';
    
    // Load the kernel
    execCommand(`kexec -l ${kernelPath} --initrd=${initrdPath} --command-line="${cmdline}"`, {
      stdio: 'inherit'
    });
    
    spinner.succeed('Kernel loaded. Ready for kexec.');
    
    console.log(chalk.yellow('\n⚠️  WARNING: About to switch to new kernel!'));
    console.log(chalk.yellow('   All running processes will be terminated.'));
    console.log(chalk.cyan('\n   To execute the switch, run:'));
    console.log(chalk.bold('   sudo kexec -e'));
    console.log('');
    
    return true;
  } catch (error) {
    spinner.fail(`kexec failed: ${error.message}`);
    return false;
  }
}

/**
 * Main switch-os command
 */
async function switchOS(targetOS, options = {}) {
  console.log(chalk.bold('\n═══════════════════════════════════════════════'));
  console.log(chalk.bold(`  OS Switcher: Switching to ${targetOS}`));
  console.log(chalk.bold('═══════════════════════════════════════════════\n'));
  
  checkRoot();
  initSwitchDirs();
  
  const targetConfig = CONFIG.targetOS[targetOS];
  if (!targetConfig) {
    console.error(chalk.red(`Unknown target OS: ${targetOS}`));
    console.log(chalk.gray('Available targets:'), Object.keys(CONFIG.targetOS).join(', '));
    process.exit(1);
  }
  
  // Step 1: Create backup snapshot
  console.log(chalk.cyan('\n[1/5] Creating backup snapshot of current OS...'));
  const snapshot = await createSnapshot(`pre-switch-${targetOS}-${Date.now()}`);
  if (!snapshot) {
    console.error(chalk.red('Failed to create backup snapshot. Aborting.'));
    process.exit(1);
  }
  
  // Step 2: Prepare target OS container
  console.log(chalk.cyan('\n[2/5] Preparing target OS container...'));
  const { stagingDir, osConfig } = await prepareTargetOS(targetOS, options.partition);
  
  // Step 3: Check target partition
  console.log(chalk.cyan('\n[3/5] Checking target partition...'));
  if (options.partition) {
    const partInfo = execCommand(`lsblk -no SIZE,FSTYPE ${options.partition}`, { throwOnError: false });
    if (partInfo) {
      console.log(chalk.gray(`  Partition: ${options.partition}`));
      console.log(chalk.gray(`  Info: ${partInfo}`));
    } else {
      console.log(chalk.yellow(`  Warning: Could not get partition info for ${options.partition}`));
    }
  } else {
    console.log(chalk.yellow('  No target partition specified. Using staging only.'));
    console.log(chalk.gray('  Use --partition=/dev/sdX to specify target.'));
  }
  
  // Step 4: Sync filesystem (if partition specified)
  if (options.partition && !options.dryRun) {
    console.log(chalk.cyan('\n[4/5] Syncing filesystem to target partition...'));
    
    const mountPoint = path.join(CONFIG.switchBase, 'mnt');
    fs.mkdirSync(mountPoint, { recursive: true });
    
    try {
      // Mount target partition
      execCommand(`mount ${options.partition} ${mountPoint}`);
      
      // Sync with rsync
      execCommand(`rsync -axHAWXS --numeric-ids --delete ${stagingDir}/ ${mountPoint}/`, {
        stdio: 'inherit'
      });
      
      // Copy kernel and initrd
      if (fs.existsSync(path.join(stagingDir, osConfig.kernel.slice(1)))) {
        console.log(chalk.gray('  Copying kernel and initrd...'));
        fs.cpSync(
          path.join(stagingDir, osConfig.kernel.slice(1)),
          path.join(mountPoint, osConfig.kernel.slice(1)),
          { recursive: true }
        );
      }
      
      // Unmount
      execCommand(`umount ${mountPoint}`);
      
      console.log(chalk.green('  ✓ Filesystem synced to target partition'));
    } catch (error) {
      execCommand(`umount ${mountPoint}`, { throwOnError: false });
      console.error(chalk.red(`  Sync failed: ${error.message}`));
    }
  } else {
    console.log(chalk.cyan('\n[4/5] Skipping filesystem sync (dry run or no partition)'));
  }
  
  // Step 5: kexec preparation
  console.log(chalk.cyan('\n[5/5] Preparing kexec...'));
  
  const kernelPath = path.join(stagingDir, osConfig.kernel.slice(1));
  const initrdPath = path.join(stagingDir, osConfig.initrd.slice(1));
  
  if (fs.existsSync(kernelPath) && fs.existsSync(initrdPath)) {
    if (!options.dryRun) {
      await performKexec(kernelPath, initrdPath);
    } else {
      console.log(chalk.yellow('  [Dry run] Would execute kexec with:'));
      console.log(chalk.gray(`    Kernel: ${kernelPath}`));
      console.log(chalk.gray(`    Initrd: ${initrdPath}`));
    }
  } else {
    console.log(chalk.yellow('  Kernel/initrd not found in container.'));
    console.log(chalk.gray('  You may need to install the kernel package in the container.'));
  }
  
  // Summary
  console.log(chalk.bold('\n═══════════════════════════════════════════════'));
  console.log(chalk.green('  OS Switch Preparation Complete'));
  console.log(chalk.bold('═══════════════════════════════════════════════'));
  console.log('');
  console.log(chalk.cyan('Backup snapshot:'), snapshot.name);
  console.log(chalk.cyan('Target OS:'), targetOS);
  console.log(chalk.cyan('Staging dir:'), stagingDir);
  
  if (!options.dryRun && checkKexecSupport()) {
    console.log('');
    console.log(chalk.yellow('To complete the switch, run:'));
    console.log(chalk.bold('  sudo kexec -e'));
    console.log('');
    console.log(chalk.gray('Or reboot to use traditional boot process.'));
  }
}

/**
 * Show status and help
 */
function showStatus() {
  console.log(chalk.bold('\n═══════════════════════════════════════════════'));
  console.log(chalk.bold('  OS Switcher Status'));
  console.log(chalk.bold('═══════════════════════════════════════════════\n'));
  
  // Current OS info
  console.log(chalk.cyan('Current System:'));
  try {
    console.log(`  OS:      ${execCommand('cat /etc/os-release | grep "^PRETTY_NAME" | cut -d= -f2 | tr -d \'"\'', { throwOnError: false }) || 'Unknown'}`);
    console.log(`  Kernel:  ${execCommand('uname -r', { throwOnError: false })}`);
    console.log(`  Arch:    ${execCommand('uname -m', { throwOnError: false })}`);
  } catch {}
  console.log('');
  
  // Snapshot method
  console.log(chalk.cyan('Snapshot Method:'));
  const method = detectSnapshotMethod();
  console.log(`  ${method ? chalk.green(method) : chalk.red('None available')}`);
  console.log('');
  
  // kexec support
  console.log(chalk.cyan('kexec Support:'));
  console.log(`  ${checkKexecSupport() ? chalk.green('Available') : chalk.red('Not installed')}`);
  console.log('');
  
  // Available targets
  console.log(chalk.cyan('Available Target OS:'));
  for (const [name, config] of Object.entries(CONFIG.targetOS)) {
    console.log(`  ${chalk.bold(name.padEnd(10))} ${chalk.gray(config.image)}`);
  }
  console.log('');
  
  // List snapshots
  listSnapshots();
}

/**
 * Print help
 */
function printHelp() {
  console.log(`
${chalk.bold('OS Switcher (pf switch-os)')}

${chalk.cyan('Usage:')}
  node tools/os-switcher.mjs <command> [options]

${chalk.cyan('Commands:')}
  ${chalk.bold('switch')} <target-os> [options]
    Switch to a new OS using container + kexec
    
    Options:
      --partition=/dev/sdX  Target partition for new OS
      --dry-run             Show what would be done without executing
    
    Example:
      switch fedora --partition=/dev/sda3
      switch arch --dry-run

  ${chalk.bold('snapshot')} [name]
    Create a snapshot of the current OS
    
    Example:
      snapshot pre-upgrade
      snapshot

  ${chalk.bold('snapshots')}
    List available snapshots

  ${chalk.bold('status')}
    Show current system status and available options

  ${chalk.bold('prepare')} <target-os>
    Prepare target OS container without switching
    Useful for inspection and customization

${chalk.cyan('Target OS Options:')}
  fedora    - Fedora Linux 40
  arch      - Arch Linux (latest)
  ubuntu    - Ubuntu 24.04 LTS
  debian    - Debian Bookworm

${chalk.cyan('Safety Features:')}
  - Automatic backup snapshot before switch
  - Dry-run mode for testing
  - kexec for rebootless switching
  - Multiple snapshot methods (btrfs, zfs, rsync)

${chalk.cyan('Environment Variables:')}
  PF_SWITCH_BASE   Base directory for operations (default: ~/.pf/os-switch)
  CONTAINER_RT     Container runtime (default: podman)

${chalk.red('⚠️  CAUTION:')}
  This tool can modify your system at a low level.
  Always have backups and test with --dry-run first.
  Requires root privileges for most operations.
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
      case 'switch': {
        const targetOS = args[1];
        if (!targetOS) {
          console.error(chalk.red('Usage: switch <target-os> [--partition=/dev/sdX] [--dry-run]'));
          process.exit(1);
        }
        
        const options = {
          partition: args.find(a => a.startsWith('--partition='))?.split('=')[1],
          dryRun: args.includes('--dry-run')
        };
        
        await switchOS(targetOS, options);
        break;
      }
      
      case 'snapshot': {
        checkRoot();
        initSwitchDirs();
        const name = args[1];
        await createSnapshot(name);
        break;
      }
      
      case 'snapshots': {
        initSwitchDirs();
        listSnapshots();
        break;
      }
      
      case 'status': {
        initSwitchDirs();
        showStatus();
        break;
      }
      
      case 'prepare': {
        checkRoot();
        initSwitchDirs();
        const targetOS = args[1];
        if (!targetOS) {
          console.error(chalk.red('Usage: prepare <target-os>'));
          process.exit(1);
        }
        await prepareTargetOS(targetOS);
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
                     process.argv[1]?.endsWith('os-switcher.mjs');

if (isMainModule) {
  main();
}

export {
  CONFIG,
  detectSnapshotMethod,
  createSnapshot,
  listSnapshots,
  prepareTargetOS,
  checkKexecSupport,
  performKexec,
  switchOS,
  showStatus
};
