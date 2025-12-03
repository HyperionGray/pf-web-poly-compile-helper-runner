#!/usr/bin/env node
/**
 * OS Switcher Tests
 * 
 * Tests the OS switching functionality including:
 * - Configuration
 * - Snapshot method detection
 * - Target OS definitions
 * - CLI interface
 */

import { fileURLToPath } from 'url';
import { dirname, join } from 'path';
import fs from 'fs';
import { execSync } from 'child_process';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const projectRoot = join(__dirname, '../..');
const toolsDir = join(projectRoot, 'tools');

// Import the module
let CONFIG, detectSnapshotMethod, checkKexecSupport;

// ANSI colors
const colors = {
  reset: '\x1b[0m',
  bright: '\x1b[1m',
  red: '\x1b[31m',
  green: '\x1b[32m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  magenta: '\x1b[35m',
  cyan: '\x1b[36m'
};

function log(color, prefix, message) {
  console.log(`${color}${prefix}${colors.reset} ${message}`);
}

let passed = 0;
let failed = 0;

function assert(condition, testName, details = '') {
  if (condition) {
    log(colors.green, '[PASS]', testName);
    passed++;
  } else {
    log(colors.red, '[FAIL]', `${testName}${details ? ': ' + details : ''}`);
    failed++;
  }
}

async function runTests() {
  console.log(`\n${colors.bright}╔════════════════════════════════════════════════════════════════╗${colors.reset}`);
  console.log(`${colors.bright}║          OS Switcher Tests                                       ║${colors.reset}`);
  console.log(`${colors.bright}╚════════════════════════════════════════════════════════════════╝${colors.reset}\n`);

  // Import module
  try {
    const module = await import(join(toolsDir, 'os-switcher.mjs'));
    CONFIG = module.CONFIG;
    detectSnapshotMethod = module.detectSnapshotMethod;
    checkKexecSupport = module.checkKexecSupport;
    log(colors.green, '[SETUP]', 'OS switcher module loaded successfully');
  } catch (e) {
    log(colors.red, '[SETUP]', `Failed to load module: ${e.message}`);
    process.exit(1);
  }

  // Test Suite: Module Configuration
  console.log(`\n${colors.cyan}Testing Module Configuration...${colors.reset}\n`);

  assert(CONFIG !== undefined, 'CONFIG is exported');
  assert(typeof CONFIG === 'object', 'CONFIG is an object');
  assert(CONFIG.targetOS !== undefined, 'CONFIG has targetOS');
  assert(CONFIG.snapshotMethods !== undefined, 'CONFIG has snapshotMethods');
  assert(typeof CONFIG.switchBase === 'string', 'CONFIG.switchBase is a string');
  assert(typeof CONFIG.runtime === 'string', 'CONFIG.runtime is a string');

  // Test Suite: Target OS Definitions
  console.log(`\n${colors.cyan}Testing Target OS Definitions...${colors.reset}\n`);

  const expectedTargets = ['fedora', 'arch', 'ubuntu', 'debian'];
  
  for (const target of expectedTargets) {
    assert(CONFIG.targetOS[target] !== undefined, `Supports ${target} target`);
    assert(CONFIG.targetOS[target].image !== undefined, `${target} has image defined`);
    assert(CONFIG.targetOS[target].kernel !== undefined, `${target} has kernel path defined`);
    assert(CONFIG.targetOS[target].initrd !== undefined, `${target} has initrd path defined`);
  }

  // Test Suite: Target OS Images
  console.log(`\n${colors.cyan}Testing Target OS Images...${colors.reset}\n`);

  assert(CONFIG.targetOS.fedora.image.includes('fedora'), 'Fedora image is correct');
  assert(CONFIG.targetOS.arch.image.includes('archlinux'), 'Arch image is correct');
  assert(CONFIG.targetOS.ubuntu.image.includes('ubuntu'), 'Ubuntu image is correct');
  assert(CONFIG.targetOS.debian.image.includes('debian'), 'Debian image is correct');

  // Test Suite: Snapshot Methods
  console.log(`\n${colors.cyan}Testing Snapshot Methods...${colors.reset}\n`);

  assert(Array.isArray(CONFIG.snapshotMethods), 'snapshotMethods is an array');
  assert(CONFIG.snapshotMethods.includes('btrfs'), 'Supports btrfs snapshots');
  assert(CONFIG.snapshotMethods.includes('zfs'), 'Supports zfs snapshots');
  assert(CONFIG.snapshotMethods.includes('rsync'), 'Supports rsync snapshots');

  // Test Suite: Snapshot Method Detection
  console.log(`\n${colors.cyan}Testing Snapshot Method Detection...${colors.reset}\n`);

  const method = detectSnapshotMethod();
  assert(
    method === null || CONFIG.snapshotMethods.includes(method),
    `Detected snapshot method is valid: ${method || 'none'}`
  );

  // Test Suite: kexec Support Check
  console.log(`\n${colors.cyan}Testing kexec Support Check...${colors.reset}\n`);

  const kexecAvailable = checkKexecSupport();
  assert(typeof kexecAvailable === 'boolean', 'checkKexecSupport returns boolean');
  log(colors.blue, '[INFO]', `kexec available: ${kexecAvailable}`);

  // Test Suite: CLI Help
  console.log(`\n${colors.cyan}Testing CLI Interface...${colors.reset}\n`);

  try {
    const helpOutput = execSync(`node ${join(toolsDir, 'os-switcher.mjs')} --help`, {
      encoding: 'utf-8',
      cwd: projectRoot
    });
    assert(helpOutput.includes('OS Switcher'), 'Help shows tool name');
    assert(helpOutput.includes('switch'), 'Help shows switch command');
    assert(helpOutput.includes('snapshot'), 'Help shows snapshot command');
    assert(helpOutput.includes('status'), 'Help shows status command');
    assert(helpOutput.includes('fedora'), 'Help mentions fedora');
    assert(helpOutput.includes('arch'), 'Help mentions arch');
    assert(helpOutput.includes('ubuntu'), 'Help mentions ubuntu');
    assert(helpOutput.includes('kexec'), 'Help mentions kexec');
    assert(helpOutput.includes('btrfs'), 'Help mentions btrfs');
    assert(helpOutput.includes('rsync'), 'Help mentions rsync');
    assert(helpOutput.includes('CAUTION'), 'Help includes caution warning');
  } catch (e) {
    log(colors.red, '[FAIL]', `CLI help test failed: ${e.message}`);
    failed += 11;
  }

  // Test Suite: Status Command
  console.log(`\n${colors.cyan}Testing Status Command...${colors.reset}\n`);

  try {
    const statusOutput = execSync(`node ${join(toolsDir, 'os-switcher.mjs')} status`, {
      encoding: 'utf-8',
      cwd: projectRoot
    });
    assert(statusOutput.includes('OS Switcher Status'), 'Status shows header');
    assert(statusOutput.includes('Current System'), 'Status shows current system');
    assert(statusOutput.includes('Snapshot Method'), 'Status shows snapshot method');
    assert(statusOutput.includes('kexec Support'), 'Status shows kexec support');
    assert(statusOutput.includes('Available Target OS'), 'Status shows available targets');
  } catch (e) {
    log(colors.red, '[FAIL]', `CLI status test failed: ${e.message}`);
    failed += 5;
  }

  // Print summary
  console.log(`\n${colors.bright}╔════════════════════════════════════════════════════════════════╗${colors.reset}`);
  console.log(`${colors.bright}║                    Test Summary                                  ║${colors.reset}`);
  console.log(`${colors.bright}╚════════════════════════════════════════════════════════════════╝${colors.reset}\n`);

  console.log(`${colors.cyan}Results:${colors.reset}`);
  console.log(`  ${colors.green}✓ Passed:${colors.reset} ${passed}`);
  console.log(`  ${colors.red}✗ Failed:${colors.reset} ${failed}`);
  console.log(`  ${colors.blue}Total:${colors.reset} ${passed + failed}`);
  console.log(`  ${colors.magenta}Success Rate:${colors.reset} ${Math.round((passed / (passed + failed)) * 100)}%`);

  if (failed === 0) {
    console.log(`\n${colors.green}${colors.bright}🎉 All tests passed!${colors.reset}`);
  } else {
    console.log(`\n${colors.yellow}⚠️  Some tests failed. Please review the results above.${colors.reset}`);
  }

  return { passed, failed };
}

// Run tests
runTests().then(result => {
  process.exit(result.failed === 0 ? 0 : 1);
}).catch(error => {
  console.error('Test runner error:', error);
  process.exit(1);
});
