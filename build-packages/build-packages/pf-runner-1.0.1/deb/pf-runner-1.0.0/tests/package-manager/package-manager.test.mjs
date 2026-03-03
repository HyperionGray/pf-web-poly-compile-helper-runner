#!/usr/bin/env node
/**
 * Package Manager Translation Tool Tests
 * 
 * Tests the package conversion functionality including:
 * - Format detection
 * - Package info extraction
 * - Hub-based conversion logic
 * - Dependency resolution
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
let PackageConverter, PackageInfo, DebHandler, RpmHandler, 
    FlatpakHandler, SnapHandler, PacmanHandler, SUPPORTED_FORMATS;

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

function assertThrows(fn, testName) {
  try {
    fn();
    log(colors.red, '[FAIL]', `${testName}: expected to throw but did not`);
    failed++;
  } catch (e) {
    log(colors.green, '[PASS]', testName);
    passed++;
  }
}

async function runTests() {
  console.log(`\n${colors.bright}╔════════════════════════════════════════════════════════════════╗${colors.reset}`);
  console.log(`${colors.bright}║          Package Manager Translation Tool Tests                  ║${colors.reset}`);
  console.log(`${colors.bright}╚════════════════════════════════════════════════════════════════╝${colors.reset}\n`);

  // Import module
  try {
    const module = await import(join(toolsDir, 'package-manager.mjs'));
    PackageConverter = module.PackageConverter;
    PackageInfo = module.PackageInfo;
    DebHandler = module.DebHandler;
    RpmHandler = module.RpmHandler;
    FlatpakHandler = module.FlatpakHandler;
    SnapHandler = module.SnapHandler;
    PacmanHandler = module.PacmanHandler;
    SUPPORTED_FORMATS = module.SUPPORTED_FORMATS;
    log(colors.green, '[SETUP]', 'Package manager module loaded successfully');
  } catch (e) {
    log(colors.red, '[SETUP]', `Failed to load module: ${e.message}`);
    process.exit(1);
  }

  // Test Suite: Module Exports
  console.log(`\n${colors.cyan}Testing Module Exports...${colors.reset}\n`);

  assert(typeof PackageConverter === 'function', 'PackageConverter is exported');
  assert(typeof PackageInfo === 'function', 'PackageInfo is exported');
  assert(typeof DebHandler === 'function', 'DebHandler is exported');
  assert(typeof RpmHandler === 'function', 'RpmHandler is exported');
  assert(typeof FlatpakHandler === 'function', 'FlatpakHandler is exported');
  assert(typeof SnapHandler === 'function', 'SnapHandler is exported');
  assert(typeof PacmanHandler === 'function', 'PacmanHandler is exported');
  assert(Array.isArray(SUPPORTED_FORMATS), 'SUPPORTED_FORMATS is an array');
  assert(SUPPORTED_FORMATS.length === 5, 'SUPPORTED_FORMATS has 5 entries');

  // Test Suite: Supported Formats
  console.log(`\n${colors.cyan}Testing Supported Formats...${colors.reset}\n`);

  assert(SUPPORTED_FORMATS.includes('deb'), 'Supports deb format');
  assert(SUPPORTED_FORMATS.includes('rpm'), 'Supports rpm format');
  assert(SUPPORTED_FORMATS.includes('flatpak'), 'Supports flatpak format');
  assert(SUPPORTED_FORMATS.includes('snap'), 'Supports snap format');
  assert(SUPPORTED_FORMATS.includes('pacman'), 'Supports pacman format');

  // Test Suite: PackageInfo Class
  console.log(`\n${colors.cyan}Testing PackageInfo Class...${colors.reset}\n`);

  const info = new PackageInfo({
    name: 'test-package',
    version: '1.0.0',
    architecture: 'amd64',
    description: 'A test package',
    dependencies: [{ name: 'dep1', version: null }],
    provides: ['test-pkg'],
    conflicts: ['conflict-pkg'],
    maintainer: 'Test <test@example.com>',
    homepage: 'https://example.com',
    license: 'MIT',
    size: 1024,
    sourceFormat: 'deb',
    files: ['/usr/bin/test']
  });

  assert(info.name === 'test-package', 'PackageInfo name is set');
  assert(info.version === '1.0.0', 'PackageInfo version is set');
  assert(info.architecture === 'amd64', 'PackageInfo architecture is set');
  assert(info.description === 'A test package', 'PackageInfo description is set');
  assert(info.dependencies.length === 1, 'PackageInfo dependencies are set');
  assert(info.provides.length === 1, 'PackageInfo provides are set');
  assert(info.conflicts.length === 1, 'PackageInfo conflicts are set');
  assert(info.maintainer === 'Test <test@example.com>', 'PackageInfo maintainer is set');
  assert(info.homepage === 'https://example.com', 'PackageInfo homepage is set');
  assert(info.license === 'MIT', 'PackageInfo license is set');
  assert(info.size === 1024, 'PackageInfo size is set');
  assert(info.sourceFormat === 'deb', 'PackageInfo sourceFormat is set');
  assert(info.files.length === 1, 'PackageInfo files are set');

  // Test toJSON method
  const json = info.toJSON();
  assert(typeof json === 'object', 'toJSON returns object');
  assert(json.name === 'test-package', 'toJSON preserves name');
  assert(json.version === '1.0.0', 'toJSON preserves version');

  // Test default values
  const emptyInfo = new PackageInfo();
  assert(emptyInfo.name === '', 'Default name is empty string');
  assert(emptyInfo.version === '', 'Default version is empty string');
  assert(emptyInfo.architecture === 'all', 'Default architecture is all');
  assert(emptyInfo.dependencies.length === 0, 'Default dependencies is empty array');

  // Test Suite: Handler Classes
  console.log(`\n${colors.cyan}Testing Handler Classes...${colors.reset}\n`);

  const debHandler = new DebHandler();
  const rpmHandler = new RpmHandler();
  const flatpakHandler = new FlatpakHandler();
  const snapHandler = new SnapHandler();
  const pacmanHandler = new PacmanHandler();

  assert(debHandler.format === 'deb', 'DebHandler has correct format');
  assert(rpmHandler.format === 'rpm', 'RpmHandler has correct format');
  assert(flatpakHandler.format === 'flatpak', 'FlatpakHandler has correct format');
  assert(snapHandler.format === 'snap', 'SnapHandler has correct format');
  assert(pacmanHandler.format === 'pacman', 'PacmanHandler has correct format');

  // Test isAvailable methods
  assert(typeof debHandler.isAvailable() === 'boolean', 'DebHandler.isAvailable returns boolean');
  assert(typeof rpmHandler.isAvailable() === 'boolean', 'RpmHandler.isAvailable returns boolean');
  assert(typeof flatpakHandler.isAvailable() === 'boolean', 'FlatpakHandler.isAvailable returns boolean');
  assert(typeof snapHandler.isAvailable() === 'boolean', 'SnapHandler.isAvailable returns boolean');
  assert(typeof pacmanHandler.isAvailable() === 'boolean', 'PacmanHandler.isAvailable returns boolean');

  // Test Suite: PackageConverter
  console.log(`\n${colors.cyan}Testing PackageConverter Class...${colors.reset}\n`);

  const converter = new PackageConverter();

  assert(converter.handlers !== undefined, 'PackageConverter has handlers');
  assert(Object.keys(converter.handlers).length === 5, 'PackageConverter has 5 handlers');

  // Test getAvailableFormats
  const availableFormats = converter.getAvailableFormats();
  assert(Array.isArray(availableFormats), 'getAvailableFormats returns array');
  log(colors.blue, '[INFO]', `Available formats: ${availableFormats.join(', ')}`);

  // Test detectFormat
  assert(converter.detectFormat('test.deb') === 'deb', 'Detects .deb extension');
  assert(converter.detectFormat('test.rpm') === 'rpm', 'Detects .rpm extension');
  assert(converter.detectFormat('test.flatpak') === 'flatpak', 'Detects .flatpak extension');
  assert(converter.detectFormat('test.snap') === 'snap', 'Detects .snap extension');
  assert(converter.detectFormat('test.pkg.tar.zst') === 'pacman', 'Detects pacman .pkg.tar.zst');
  assert(converter.detectFormat('test.pkg.tar.xz') === 'pacman', 'Detects pacman .pkg.tar.xz');

  // Test generateOutputPath
  const testInfo = new PackageInfo({
    name: 'myapp',
    version: '2.0.0',
    architecture: 'amd64'
  });

  const debOutput = converter.generateOutputPath('/tmp/myapp.rpm', 'deb', testInfo);
  const rpmOutput = converter.generateOutputPath('/tmp/myapp.deb', 'rpm', testInfo);
  const snapOutput = converter.generateOutputPath('/tmp/myapp.deb', 'snap', testInfo);

  assert(debOutput.endsWith('.deb'), 'generateOutputPath creates .deb path');
  assert(rpmOutput.endsWith('.rpm'), 'generateOutputPath creates .rpm path');
  assert(snapOutput.endsWith('.snap'), 'generateOutputPath creates .snap path');
  assert(debOutput.includes('myapp'), 'generateOutputPath includes package name');
  assert(debOutput.includes('2.0.0'), 'generateOutputPath includes version');

  // Test Suite: Architecture Conversion
  console.log(`\n${colors.cyan}Testing Architecture Conversion...${colors.reset}\n`);

  // RPM architecture conversion
  assert(rpmHandler.convertArch('x86_64') === 'amd64', 'RPM x86_64 → amd64');
  assert(rpmHandler.convertArch('noarch') === 'all', 'RPM noarch → all');
  assert(rpmHandler.convertArch('aarch64') === 'arm64', 'RPM aarch64 → arm64');
  assert(rpmHandler.convertArchToRpm('amd64') === 'x86_64', 'DEB amd64 → RPM x86_64');
  assert(rpmHandler.convertArchToRpm('all') === 'noarch', 'DEB all → RPM noarch');

  // Pacman architecture conversion
  assert(pacmanHandler.convertArch('x86_64') === 'amd64', 'Pacman x86_64 → amd64');
  assert(pacmanHandler.convertArch('any') === 'all', 'Pacman any → all');
  assert(pacmanHandler.convertArchToPacman('amd64') === 'x86_64', 'DEB amd64 → Pacman x86_64');
  assert(pacmanHandler.convertArchToPacman('all') === 'any', 'DEB all → Pacman any');

  // Test Suite: Dependency Parsing
  console.log(`\n${colors.cyan}Testing Dependency Parsing...${colors.reset}\n`);

  const deps1 = debHandler.parseDependencies('libc6 (>= 2.17), libssl1.1');
  assert(deps1.length === 2, 'Parses two dependencies');
  assert(deps1[0].name === 'libc6', 'First dependency name is correct');
  assert(deps1[0].version === '>= 2.17', 'First dependency version is correct');
  assert(deps1[1].name === 'libssl1.1', 'Second dependency name is correct');
  assert(deps1[1].version === null, 'Second dependency has no version');

  const deps2 = debHandler.parseDependencies('');
  assert(deps2.length === 0, 'Empty string returns empty array');

  const deps3 = debHandler.parseDependencies('single-dep');
  assert(deps3.length === 1, 'Single dependency parsed');
  assert(deps3[0].name === 'single-dep', 'Single dependency name is correct');

  // Test Suite: CLI Help
  console.log(`\n${colors.cyan}Testing CLI Interface...${colors.reset}\n`);

  try {
    const helpOutput = execSync(`node ${join(toolsDir, 'package-manager.mjs')} --help`, {
      encoding: 'utf-8',
      cwd: projectRoot
    });
    assert(helpOutput.includes('Package Manager Translation Tool'), 'Help shows tool name');
    assert(helpOutput.includes('convert'), 'Help shows convert command');
    assert(helpOutput.includes('info'), 'Help shows info command');
    assert(helpOutput.includes('deps'), 'Help shows deps command');
    assert(helpOutput.includes('formats'), 'Help shows formats command');
    assert(helpOutput.includes('matrix'), 'Help shows matrix command');
    assert(helpOutput.includes('deb'), 'Help mentions deb format');
    assert(helpOutput.includes('rpm'), 'Help mentions rpm format');
    assert(helpOutput.includes('hub'), 'Help mentions hub format');
  } catch (e) {
    log(colors.red, '[FAIL]', `CLI help test failed: ${e.message}`);
    failed += 8;
  }

  // Test formats command
  try {
    const formatsOutput = execSync(`node ${join(toolsDir, 'package-manager.mjs')} formats`, {
      encoding: 'utf-8',
      cwd: projectRoot
    });
    assert(formatsOutput.includes('Package Format Support'), 'Formats shows header');
    assert(formatsOutput.includes('deb'), 'Formats shows deb');
    assert(formatsOutput.includes('rpm'), 'Formats shows rpm');
  } catch (e) {
    log(colors.red, '[FAIL]', `CLI formats test failed: ${e.message}`);
    failed += 3;
  }

  // Test matrix command
  try {
    const matrixOutput = execSync(`node ${join(toolsDir, 'package-manager.mjs')} matrix`, {
      encoding: 'utf-8',
      cwd: projectRoot
    });
    assert(matrixOutput.includes('Conversion Matrix'), 'Matrix shows header');
    assert(matrixOutput.includes('hub format'), 'Matrix mentions hub format');
    assert(matrixOutput.includes('deb'), 'Matrix shows deb');
  } catch (e) {
    log(colors.red, '[FAIL]', `CLI matrix test failed: ${e.message}`);
    failed += 3;
  }

  // Test Suite: Conversion Logic (Hub Pattern)
  console.log(`\n${colors.cyan}Testing Hub Conversion Pattern...${colors.reset}\n`);

  // Verify the hub pattern is documented
  log(colors.blue, '[INFO]', 'Hub pattern: all formats → deb → all formats');
  
  // Test that same format conversion is handled
  try {
    const result = await converter.convert('/nonexistent.deb', 'deb');
    // This should fail because file doesn't exist, but we're testing the logic path
  } catch (e) {
    // Expected to fail because file doesn't exist
    assert(e.message.includes('Could not detect') || e.message.includes('Failed'), 
      'Same format conversion handles missing file gracefully');
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
