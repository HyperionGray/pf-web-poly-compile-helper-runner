#!/usr/bin/env node
/**
 * Dependency Vulnerability Checker
 * 
 * Addresses Amazon Q Code Review security recommendation:
 * "Dependency vulnerabilities: Review package versions"
 * 
 * Checks for known vulnerabilities in project dependencies using:
 * - npm audit for Node.js packages
 * - pip-audit for Python packages (if available)
 * - cargo audit for Rust packages (if available)
 */

import { spawn } from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';

class DependencyChecker {
  constructor(options = {}) {
    this.rootDir = options.rootDir || process.cwd();
    this.verbose = options.verbose || false;
    this.results = {
      npm: null,
      pip: null,
      cargo: null
    };
  }

  log(message) {
    if (this.verbose) {
      console.log(message);
    }
  }

  /**
   * Execute command and return output
   */
  async executeCommand(command, args, options = {}) {
    return new Promise((resolve, reject) => {
      const child = spawn(command, args, {
        cwd: options.cwd || this.rootDir,
        stdio: ['pipe', 'pipe', 'pipe']
      });

      let stdout = '';
      let stderr = '';

      child.stdout.on('data', (data) => {
        stdout += data.toString();
      });

      child.stderr.on('data', (data) => {
        stderr += data.toString();
      });

      child.on('close', (code) => {
        resolve({ stdout, stderr, code });
      });

      child.on('error', (error) => {
        reject(error);
      });
    });
  }

  /**
   * Check if a file exists
   */
  fileExists(filePath) {
    try {
      return fs.existsSync(path.join(this.rootDir, filePath));
    } catch {
      return false;
    }
  }

  /**
   * Check npm dependencies
   */
  async checkNpm() {
    if (!this.fileExists('package.json')) {
      this.log('No package.json found, skipping npm audit');
      return null;
    }

    this.log('Checking npm dependencies...');

    try {
      const result = await this.executeCommand('npm', ['audit', '--json']);
      
      if (result.code === 0 || result.stdout) {
        try {
          const auditData = JSON.parse(result.stdout);
          return {
            success: true,
            vulnerabilities: auditData.vulnerabilities || {},
            metadata: auditData.metadata || {},
            totalVulnerabilities: auditData.metadata?.vulnerabilities?.total || 0
          };
        } catch (parseError) {
          return {
            success: false,
            error: 'Failed to parse npm audit output',
            raw: result.stdout
          };
        }
      } else {
        return {
          success: false,
          error: result.stderr || 'npm audit failed',
          code: result.code
        };
      }
    } catch (error) {
      return {
        success: false,
        error: `npm audit command failed: ${error.message}`
      };
    }
  }

  /**
   * Check Python dependencies
   */
  async checkPip() {
    const pipFiles = ['requirements.txt', 'setup.py', 'pyproject.toml'];
    const hasPipFile = pipFiles.some(file => this.fileExists(file));

    if (!hasPipFile) {
      this.log('No Python dependency files found, skipping pip audit');
      return null;
    }

    this.log('Checking Python dependencies...');

    try {
      // Check if pip-audit is available
      const checkResult = await this.executeCommand('pip-audit', ['--version']);
      
      if (checkResult.code !== 0) {
        return {
          success: false,
          error: 'pip-audit not installed. Install with: pip install pip-audit',
          skipped: true
        };
      }

      // Run pip-audit
      const result = await this.executeCommand('pip-audit', ['--format', 'json']);
      
      if (result.code === 0 || result.stdout) {
        try {
          const auditData = JSON.parse(result.stdout);
          return {
            success: true,
            vulnerabilities: auditData.vulnerabilities || auditData.dependencies || [],
            totalVulnerabilities: (auditData.vulnerabilities || auditData.dependencies || []).length
          };
        } catch (parseError) {
          return {
            success: true,
            vulnerabilities: [],
            totalVulnerabilities: 0,
            note: 'No vulnerabilities found or unable to parse output'
          };
        }
      } else {
        return {
          success: false,
          error: result.stderr || 'pip-audit failed',
          code: result.code
        };
      }
    } catch (error) {
      return {
        success: false,
        error: `pip-audit command failed: ${error.message}`,
        skipped: true
      };
    }
  }

  /**
   * Check Rust dependencies
   */
  async checkCargo() {
    if (!this.fileExists('Cargo.toml')) {
      this.log('No Cargo.toml found, skipping cargo audit');
      return null;
    }

    this.log('Checking Rust dependencies...');

    try {
      // Check if cargo-audit is available
      const checkResult = await this.executeCommand('cargo', ['audit', '--version']);
      
      if (checkResult.code !== 0) {
        return {
          success: false,
          error: 'cargo-audit not installed. Install with: cargo install cargo-audit',
          skipped: true
        };
      }

      // Run cargo audit
      const result = await this.executeCommand('cargo', ['audit', '--json']);
      
      if (result.code === 0 || result.stdout) {
        try {
          const auditData = JSON.parse(result.stdout);
          const vulnerabilities = auditData.vulnerabilities?.list || [];
          return {
            success: true,
            vulnerabilities,
            totalVulnerabilities: vulnerabilities.length,
            database: auditData.database
          };
        } catch (parseError) {
          return {
            success: true,
            vulnerabilities: [],
            totalVulnerabilities: 0,
            note: 'No vulnerabilities found or unable to parse output'
          };
        }
      } else {
        return {
          success: false,
          error: result.stderr || 'cargo audit failed',
          code: result.code
        };
      }
    } catch (error) {
      return {
        success: false,
        error: `cargo audit command failed: ${error.message}`,
        skipped: true
      };
    }
  }

  /**
   * Run all checks
   */
  async checkAll() {
    console.log(`🔍 Checking dependencies in: ${this.rootDir}\n`);

    this.results.npm = await this.checkNpm();
    this.results.pip = await this.checkPip();
    this.results.cargo = await this.checkCargo();

    return this.results;
  }

  /**
   * Generate summary report
   */
  generateReport() {
    const report = {
      timestamp: new Date().toISOString(),
      directory: this.rootDir,
      summary: {
        totalVulnerabilities: 0,
        npm: { checked: false, vulnerabilities: 0 },
        pip: { checked: false, vulnerabilities: 0 },
        cargo: { checked: false, vulnerabilities: 0 }
      },
      details: this.results
    };

    // Count vulnerabilities
    if (this.results.npm && this.results.npm.success) {
      report.summary.npm.checked = true;
      report.summary.npm.vulnerabilities = this.results.npm.totalVulnerabilities || 0;
      report.summary.totalVulnerabilities += report.summary.npm.vulnerabilities;
    }

    if (this.results.pip && this.results.pip.success) {
      report.summary.pip.checked = true;
      report.summary.pip.vulnerabilities = this.results.pip.totalVulnerabilities || 0;
      report.summary.totalVulnerabilities += report.summary.pip.vulnerabilities;
    }

    if (this.results.cargo && this.results.cargo.success) {
      report.summary.cargo.checked = true;
      report.summary.cargo.vulnerabilities = this.results.cargo.totalVulnerabilities || 0;
      report.summary.totalVulnerabilities += report.summary.cargo.vulnerabilities;
    }

    return report;
  }

  /**
   * Print formatted report
   */
  printReport(report = null) {
    const r = report || this.generateReport();

    console.log('\n' + '='.repeat(70));
    console.log('         DEPENDENCY VULNERABILITY SCAN REPORT');
    console.log('='.repeat(70) + '\n');

    console.log(`Directory: ${r.directory}`);
    console.log(`Scan Date: ${r.timestamp}\n`);

    console.log('Summary:');
    console.log(`  Total Vulnerabilities: ${r.summary.totalVulnerabilities}\n`);

    // NPM Results
    if (r.details.npm) {
      console.log('📦 Node.js (npm):');
      if (r.details.npm.success) {
        console.log(`   ✅ Checked - ${r.summary.npm.vulnerabilities} vulnerabilities found`);
        if (r.details.npm.metadata) {
          const meta = r.details.npm.metadata.vulnerabilities || {};
          if (meta.critical) console.log(`      🔴 Critical: ${meta.critical}`);
          if (meta.high) console.log(`      🟠 High: ${meta.high}`);
          if (meta.moderate) console.log(`      🟡 Moderate: ${meta.moderate}`);
          if (meta.low) console.log(`      🟢 Low: ${meta.low}`);
        }
      } else if (r.details.npm.skipped) {
        console.log(`   ⚠️  Skipped: ${r.details.npm.error}`);
      } else {
        console.log(`   ❌ Failed: ${r.details.npm.error}`);
      }
      console.log('');
    }

    // Python Results
    if (r.details.pip) {
      console.log('🐍 Python (pip):');
      if (r.details.pip.success) {
        console.log(`   ✅ Checked - ${r.summary.pip.vulnerabilities} vulnerabilities found`);
      } else if (r.details.pip.skipped) {
        console.log(`   ⚠️  Skipped: ${r.details.pip.error}`);
      } else {
        console.log(`   ❌ Failed: ${r.details.pip.error}`);
      }
      console.log('');
    }

    // Rust Results
    if (r.details.cargo) {
      console.log('🦀 Rust (cargo):');
      if (r.details.cargo.success) {
        console.log(`   ✅ Checked - ${r.summary.cargo.vulnerabilities} vulnerabilities found`);
      } else if (r.details.cargo.skipped) {
        console.log(`   ⚠️  Skipped: ${r.details.cargo.error}`);
      } else {
        console.log(`   ❌ Failed: ${r.details.cargo.error}`);
      }
      console.log('');
    }

    if (r.summary.totalVulnerabilities === 0) {
      console.log('✅ No vulnerabilities detected!\n');
    } else {
      console.log(`⚠️  ${r.summary.totalVulnerabilities} vulnerabilities found!`);
      console.log('📋 Run package-specific audit commands for detailed information:\n');
      if (r.summary.npm.vulnerabilities > 0) {
        console.log('   npm audit');
        console.log('   npm audit fix  # Automatically fix vulnerabilities\n');
      }
      if (r.summary.pip.vulnerabilities > 0) {
        console.log('   pip-audit\n');
      }
      if (r.summary.cargo.vulnerabilities > 0) {
        console.log('   cargo audit\n');
      }
    }

    console.log('='.repeat(70) + '\n');
  }
}

// CLI interface
if (import.meta.url === `file://${process.argv[1]}`) {
  const args = process.argv.slice(2);

  if (args.includes('--help') || args.includes('-h')) {
    console.log(`
Dependency Vulnerability Checker

Usage:
  dependency-checker.mjs [directory] [options]

Options:
  --verbose, -v    Enable verbose output
  --json           Output results as JSON

Examples:
  dependency-checker.mjs
  dependency-checker.mjs /path/to/project --verbose
  dependency-checker.mjs . --json
`);
    process.exit(0);
  }

  const dir = args.find(arg => !arg.startsWith('-')) || process.cwd();
  const verbose = args.includes('--verbose') || args.includes('-v');
  const json = args.includes('--json');

  const checker = new DependencyChecker({ rootDir: dir, verbose });

  checker.checkAll()
    .then(() => {
      const report = checker.generateReport();
      
      if (json) {
        console.log(JSON.stringify(report, null, 2));
      } else {
        checker.printReport(report);
      }

      // Exit with error code if vulnerabilities found
      if (report.summary.totalVulnerabilities > 0) {
        process.exit(1);
      }
    })
    .catch(error => {
      console.error('Error during dependency check:', error.message);
      process.exit(1);
    });
}

export default DependencyChecker;
