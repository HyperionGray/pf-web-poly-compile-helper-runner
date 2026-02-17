#!/usr/bin/env node
/**
 * Distro Container Manager Tests
 * 
 * Tests the distro container management functionality including:
 * - Configuration
 * - Directory initialization
 * - Distro detection
 * - View mode switching
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
let CONFIG, initArtifactDirs, getContainerRuntime;

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
  console.log(`${colors.bright}║          Distro Container Manager Tests                         ║${colors.reset}`);
  console.log(`${colors.bright}╚════════════════════════════════════════════════════════════════╝${colors.reset}\n`);

  // Import module
  try {
    const module = await import(join(toolsDir, 'distro-container-manager.mjs'));
    CONFIG = module.CONFIG;
    initArtifactDirs = module.initArtifactDirs;
    getContainerRuntime = module.getContainerRuntime;
    log(colors.green, '[SETUP]', 'Distro container manager module loaded successfully');
  } catch (e) {
    log(colors.red, '[SETUP]', `Failed to load module: ${e.message}`);
    process.exit(1);
  }

  // Test Suite: Module Exports
  console.log(`\n${colors.cyan}Testing Module Configuration...${colors.reset}\n`);

  assert(CONFIG !== undefined, 'CONFIG is exported');
  assert(typeof CONFIG === 'object', 'CONFIG is an object');
  assert(CONFIG.distros !== undefined, 'CONFIG has distros');
  assert(CONFIG.viewModes !== undefined, 'CONFIG has viewModes');
  assert(typeof CONFIG.artifactBase === 'string', 'CONFIG.artifactBase is a string');
  assert(typeof CONFIG.runtime === 'string', 'CONFIG.runtime is a string');

  // Test Suite: Supported Distros
  console.log(`\n${colors.cyan}Testing Supported Distros...${colors.reset}\n`);

  const expectedDistros = ['fedora', 'centos', 'arch', 'opensuse'];
  
  for (const distro of expectedDistros) {
    assert(CONFIG.distros[distro] !== undefined, `Supports ${distro} distro`);
    assert(CONFIG.distros[distro].image !== undefined, `${distro} has image defined`);
    assert(CONFIG.distros[distro].dockerfile !== undefined, `${distro} has dockerfile defined`);
    assert(CONFIG.distros[distro].packageManager !== undefined, `${distro} has packageManager defined`);
  }

  // Test Suite: Distro Package Managers
  console.log(`\n${colors.cyan}Testing Distro Package Managers...${colors.reset}\n`);

  assert(CONFIG.distros.fedora.packageManager === 'dnf', 'Fedora uses dnf');
  assert(CONFIG.distros.centos.packageManager === 'dnf', 'CentOS uses dnf');
  assert(CONFIG.distros.arch.packageManager === 'pacman', 'Arch uses pacman');
  assert(CONFIG.distros.opensuse.packageManager === 'zypper', 'openSUSE uses zypper');

  // Test Suite: View Modes
  console.log(`\n${colors.cyan}Testing View Modes...${colors.reset}\n`);

  assert(Array.isArray(CONFIG.viewModes), 'viewModes is an array');
  assert(CONFIG.viewModes.includes('unified'), 'Supports unified view mode');
  assert(CONFIG.viewModes.includes('isolated'), 'Supports isolated view mode');

  // Test Suite: Dockerfiles Exist
  console.log(`\n${colors.cyan}Testing Dockerfile Availability...${colors.reset}\n`);

  const dockerfilesDir = join(projectRoot, 'containers/dockerfiles');
  
  for (const [name, distro] of Object.entries(CONFIG.distros)) {
    const dockerfilePath = join(dockerfilesDir, distro.dockerfile);
    const exists = fs.existsSync(dockerfilePath);
    assert(exists, `Dockerfile exists for ${name}: ${distro.dockerfile}`);
  }

  // Test Suite: CLI Help
  console.log(`\n${colors.cyan}Testing CLI Interface...${colors.reset}\n`);

  try {
    const helpOutput = execSync(`node ${join(toolsDir, 'distro-container-manager.mjs')} --help`, {
      encoding: 'utf-8',
      cwd: projectRoot
    });
    assert(helpOutput.includes('Distro Container Manager'), 'Help shows tool name');
    assert(helpOutput.includes('install'), 'Help shows install command');
    assert(helpOutput.includes('switch'), 'Help shows switch command');
    assert(helpOutput.includes('view'), 'Help shows view command');
    assert(helpOutput.includes('build'), 'Help shows build command');
    assert(helpOutput.includes('status'), 'Help shows status command');
    assert(helpOutput.includes('fedora'), 'Help mentions fedora');
    assert(helpOutput.includes('arch'), 'Help mentions arch');
    assert(helpOutput.includes('rshared'), 'Help mentions rshared mounts');
  } catch (e) {
    log(colors.red, '[FAIL]', `CLI help test failed: ${e.message}`);
    failed += 8;
  }

  // Test Suite: Init Command
  console.log(`\n${colors.cyan}Testing Init Command...${colors.reset}\n`);

  // Use a temporary directory for testing
  const testArtifactBase = `/tmp/pf-distro-test-${Date.now()}`;
  
  try {
    // Temporarily override CONFIG
    const origBase = CONFIG.artifactBase;
    CONFIG.artifactBase = testArtifactBase;
    
    initArtifactDirs();
    
    assert(fs.existsSync(testArtifactBase), 'Artifact base directory created');
    assert(fs.existsSync(join(testArtifactBase, 'fedora/bin')), 'Fedora bin directory created');
    assert(fs.existsSync(join(testArtifactBase, 'centos/bin')), 'CentOS bin directory created');
    assert(fs.existsSync(join(testArtifactBase, 'arch/bin')), 'Arch bin directory created');
    assert(fs.existsSync(join(testArtifactBase, 'opensuse/bin')), 'openSUSE bin directory created');
    assert(fs.existsSync(join(testArtifactBase, 'unified/bin')), 'Unified bin directory created');
    assert(fs.existsSync(join(testArtifactBase, 'config.json')), 'Config file created');
    
    // Check config file structure
    const config = JSON.parse(fs.readFileSync(join(testArtifactBase, 'config.json'), 'utf-8'));
    assert(config.viewMode !== undefined, 'Config has viewMode');
    assert(config.installedPackages !== undefined, 'Config has installedPackages');
    assert(config.viewMode === 'unified', 'Default view mode is unified');
    
    // Cleanup
    fs.rmSync(testArtifactBase, { recursive: true, force: true });
    CONFIG.artifactBase = origBase;
    
  } catch (e) {
    log(colors.red, '[FAIL]', `Init test failed: ${e.message}`);
    failed += 9;
  }

  // Test Suite: Container Runtime Detection
  console.log(`\n${colors.cyan}Testing Container Runtime Detection...${colors.reset}\n`);

  try {
    const runtime = getContainerRuntime();
    assert(
      runtime === 'podman' || runtime === 'docker',
      `Container runtime detected: ${runtime}`
    );
  } catch (e) {
    log(colors.yellow, '[SKIP]', `Container runtime not available: ${e.message}`);
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
