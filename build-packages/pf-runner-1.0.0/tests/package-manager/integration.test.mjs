#!/usr/bin/env node
/**
 * Integration Tests for Package Manager Translation Tool
 * 
 * Tests real package operations when tools are available:
 * - Creating test packages
 * - Converting between formats
 * - Extracting and verifying contents
 */

import { fileURLToPath } from 'url';
import { dirname, join } from 'path';
import fs from 'fs';
import { execSync } from 'child_process';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const projectRoot = join(__dirname, '../..');
const toolsDir = join(projectRoot, 'tools');

// ANSI colors
const colors = {
  reset: '\x1b[0m',
  bright: '\x1b[1m',
  red: '\x1b[31m',
  green: '\x1b[32m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  cyan: '\x1b[36m'
};

function log(color, prefix, message) {
  console.log(`${color}${prefix}${colors.reset} ${message}`);
}

let passed = 0;
let failed = 0;
let skipped = 0;

function assert(condition, testName, details = '') {
  if (condition) {
    log(colors.green, '[PASS]', testName);
    passed++;
  } else {
    log(colors.red, '[FAIL]', `${testName}${details ? ': ' + details : ''}`);
    failed++;
  }
}

function skip(testName, reason) {
  log(colors.yellow, '[SKIP]', `${testName}: ${reason}`);
  skipped++;
}

function commandExists(cmd) {
  try {
    execSync(`which ${cmd}`, { encoding: 'utf-8', stdio: 'pipe' });
    return true;
  } catch {
    return false;
  }
}

async function runIntegrationTests() {
  console.log(`\n${colors.bright}╔════════════════════════════════════════════════════════════════╗${colors.reset}`);
  console.log(`${colors.bright}║      Package Manager Integration Tests                           ║${colors.reset}`);
  console.log(`${colors.bright}╚════════════════════════════════════════════════════════════════╝${colors.reset}\n`);

  // Create temp directory
  const tempDir = fs.mkdtempSync('/tmp/pkg-test-');
  log(colors.blue, '[SETUP]', `Created temp directory: ${tempDir}`);

  try {
    // Import module
    const module = await import(join(toolsDir, 'package-manager.mjs'));
    const { PackageConverter, PackageInfo, DebHandler, RpmHandler } = module;
    
    const converter = new PackageConverter();
    const availableFormats = converter.getAvailableFormats();
    
    log(colors.blue, '[INFO]', `Available formats: ${availableFormats.join(', ')}`);

    // Test Suite: DEB Handler Integration
    console.log(`\n${colors.cyan}Testing DEB Handler Integration...${colors.reset}\n`);

    if (availableFormats.includes('deb')) {
      // Create a minimal test .deb package
      const debTestDir = join(tempDir, 'deb-test');
      const debControlDir = join(debTestDir, 'DEBIAN');
      const debBinDir = join(debTestDir, 'usr', 'bin');
      
      fs.mkdirSync(debControlDir, { recursive: true });
      fs.mkdirSync(debBinDir, { recursive: true });

      // Create control file
      const controlContent = `Package: test-package
Version: 1.0.0
Architecture: all
Maintainer: Test <test@example.com>
Description: A test package for integration testing
Depends: bash
`;
      fs.writeFileSync(join(debControlDir, 'control'), controlContent);

      // Create a test script
      fs.writeFileSync(join(debBinDir, 'test-script'), '#!/bin/bash\necho "Hello from test package"');
      fs.chmodSync(join(debBinDir, 'test-script'), 0o755);

      // Build the .deb
      const debPath = join(tempDir, 'test-package_1.0.0_all.deb');
      try {
        execSync(`dpkg-deb --build "${debTestDir}" "${debPath}"`, { stdio: 'pipe' });
        assert(fs.existsSync(debPath), 'DEB package created successfully');

        // Test info extraction
        const debHandler = new DebHandler();
        const info = await debHandler.extractInfo(debPath);
        
        assert(info.name === 'test-package', 'DEB info: name extracted correctly');
        assert(info.version === '1.0.0', 'DEB info: version extracted correctly');
        assert(info.architecture === 'all', 'DEB info: architecture extracted correctly');
        assert(info.description.includes('test package'), 'DEB info: description extracted correctly');
        assert(info.dependencies.length > 0, 'DEB info: dependencies extracted');
        assert(info.dependencies[0].name === 'bash', 'DEB info: dependency name correct');

        // Test content extraction
        const extractDir = join(tempDir, 'deb-extract');
        await debHandler.extractContents(debPath, extractDir);
        
        assert(fs.existsSync(join(extractDir, 'usr', 'bin', 'test-script')), 'DEB extraction: files extracted correctly');
        assert(fs.existsSync(join(extractDir, 'DEBIAN', 'control')), 'DEB extraction: control file extracted');

      } catch (e) {
        log(colors.red, '[ERROR]', `DEB test failed: ${e.message}`);
        failed += 6;
      }
    } else {
      skip('DEB integration tests', 'dpkg not available');
    }

    // Test Suite: RPM Handler Integration
    console.log(`\n${colors.cyan}Testing RPM Handler Integration...${colors.reset}\n`);

    if (availableFormats.includes('rpm')) {
      // Find the .deb file we created
      const debPath = join(tempDir, 'test-package_1.0.0_all.deb');
      
      if (fs.existsSync(debPath)) {
        const rpmHandler = new RpmHandler();
        
        // Test rpm2cpio extraction if available
        if (commandExists('rpm2cpio')) {
          // We can't create RPM easily, but we can test the handler methods
          assert(typeof rpmHandler.convertArch === 'function', 'RPM handler has convertArch method');
          assert(rpmHandler.convertArch('x86_64') === 'amd64', 'RPM arch conversion works');
          assert(rpmHandler.convertArchToRpm('amd64') === 'x86_64', 'RPM reverse arch conversion works');
        } else {
          skip('RPM content tests', 'rpm2cpio not available');
        }
      } else {
        skip('RPM integration tests', 'No .deb package to convert');
      }
    } else {
      skip('RPM integration tests', 'RPM tools not available');
    }

    // Test Suite: Format Detection
    console.log(`\n${colors.cyan}Testing Format Detection...${colors.reset}\n`);

    // Test with actual file if we created one
    const debPath = join(tempDir, 'test-package_1.0.0_all.deb');
    if (fs.existsSync(debPath)) {
      const detectedFormat = converter.detectFormat(debPath);
      assert(detectedFormat === 'deb', 'Format detection: detects .deb file');
    }

    // Test file extension detection
    assert(converter.detectFormat('/test/package.rpm') === 'rpm', 'Format detection: .rpm extension');
    assert(converter.detectFormat('/test/app.flatpak') === 'flatpak', 'Format detection: .flatpak extension');
    assert(converter.detectFormat('/test/app.snap') === 'snap', 'Format detection: .snap extension');
    assert(converter.detectFormat('/test/pkg-1.0-1-x86_64.pkg.tar.zst') === 'pacman', 'Format detection: .pkg.tar.zst');

    // Test Suite: Output Path Generation
    console.log(`\n${colors.cyan}Testing Output Path Generation...${colors.reset}\n`);

    const testInfo = new PackageInfo({
      name: 'myapp',
      version: '2.0.0',
      architecture: 'amd64'
    });

    const debOutput = converter.generateOutputPath('/tmp/myapp.rpm', 'deb', testInfo);
    assert(debOutput === '/tmp/myapp_2.0.0_amd64.deb', 'Output path: correct .deb path');

    const rpmOutput = converter.generateOutputPath('/tmp/myapp.deb', 'rpm', testInfo);
    assert(rpmOutput === '/tmp/myapp-2.0.0.amd64.rpm', 'Output path: correct .rpm path');

    const snapOutput = converter.generateOutputPath('/tmp/myapp.deb', 'snap', testInfo);
    assert(snapOutput === '/tmp/myapp_2.0.0_amd64.snap', 'Output path: correct .snap path');

    const pacmanOutput = converter.generateOutputPath('/tmp/myapp.deb', 'pacman', testInfo);
    assert(pacmanOutput === '/tmp/myapp-2.0.0-amd64.pkg.tar.zst', 'Output path: correct pacman path');

    // Test Suite: CLI Commands
    console.log(`\n${colors.cyan}Testing CLI Commands...${colors.reset}\n`);

    // Test formats command
    try {
      const formatsOutput = execSync(`node ${join(toolsDir, 'package-manager.mjs')} formats`, {
        encoding: 'utf-8',
        cwd: projectRoot
      });
      assert(formatsOutput.includes('deb'), 'CLI formats: shows deb');
      assert(formatsOutput.includes('rpm'), 'CLI formats: shows rpm');
    } catch (e) {
      log(colors.red, '[FAIL]', `CLI formats test failed: ${e.message}`);
      failed += 2;
    }

    // Test matrix command
    try {
      const matrixOutput = execSync(`node ${join(toolsDir, 'package-manager.mjs')} matrix`, {
        encoding: 'utf-8',
        cwd: projectRoot
      });
      assert(matrixOutput.includes('hub format'), 'CLI matrix: mentions hub format');
    } catch (e) {
      log(colors.red, '[FAIL]', `CLI matrix test failed: ${e.message}`);
      failed += 1;
    }

    // Test info command with our test package
    if (fs.existsSync(debPath)) {
      try {
        const infoOutput = execSync(`node ${join(toolsDir, 'package-manager.mjs')} info "${debPath}"`, {
          encoding: 'utf-8',
          cwd: projectRoot
        });
        assert(infoOutput.includes('test-package'), 'CLI info: shows package name');
        assert(infoOutput.includes('1.0.0'), 'CLI info: shows version');
      } catch (e) {
        log(colors.red, '[FAIL]', `CLI info test failed: ${e.message}`);
        failed += 2;
      }
    }

  } finally {
    // Cleanup
    try {
      execSync(`rm -rf "${tempDir}"`, { stdio: 'pipe' });
      log(colors.blue, '[CLEANUP]', 'Removed temp directory');
    } catch (e) {
      log(colors.yellow, '[WARN]', `Could not clean up: ${e.message}`);
    }
  }

  // Print summary
  console.log(`\n${colors.bright}╔════════════════════════════════════════════════════════════════╗${colors.reset}`);
  console.log(`${colors.bright}║                Integration Test Summary                          ║${colors.reset}`);
  console.log(`${colors.bright}╚════════════════════════════════════════════════════════════════╝${colors.reset}\n`);

  console.log(`${colors.cyan}Results:${colors.reset}`);
  console.log(`  ${colors.green}✓ Passed:${colors.reset}  ${passed}`);
  console.log(`  ${colors.red}✗ Failed:${colors.reset}  ${failed}`);
  console.log(`  ${colors.yellow}○ Skipped:${colors.reset} ${skipped}`);
  console.log(`  ${colors.blue}Total:${colors.reset}    ${passed + failed + skipped}`);

  if (failed === 0) {
    console.log(`\n${colors.green}${colors.bright}🎉 All integration tests passed!${colors.reset}`);
    if (skipped > 0) {
      console.log(`${colors.yellow}ℹ️  Some tests were skipped due to missing tools.${colors.reset}`);
    }
  } else {
    console.log(`\n${colors.yellow}⚠️  Some integration tests failed.${colors.reset}`);
  }

  return { passed, failed, skipped };
}

// Run tests
runIntegrationTests().then(result => {
  process.exit(result.failed === 0 ? 0 : 1);
}).catch(error => {
  console.error('Test runner error:', error);
  process.exit(1);
});
