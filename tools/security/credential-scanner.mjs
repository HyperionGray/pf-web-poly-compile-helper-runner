#!/usr/bin/env node
/**
 * Credential Scanner Tool
 * Scans codebase for hardcoded secrets, API keys, passwords, and other sensitive data
 * 
 * Addresses Amazon Q Code Review security recommendation:
 * "Credential scanning: Check for hardcoded secrets"
 */

import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Patterns to detect various types of secrets
const SECRET_PATTERNS = [
  {
    name: 'Generic API Key',
    pattern: /(?:api[_-]?key|apikey)[\s]*[:=][\s]*['"]([a-zA-Z0-9_\-]{20,})['"]|/gi,
    severity: 'high'
  },
  {
    name: 'Generic Secret',
    pattern: /(?:secret|token)[\s]*[:=][\s]*['"]([a-zA-Z0-9_\-]{20,})['"]|/gi,
    severity: 'high'
  },
  {
    name: 'Password',
    pattern: /(?:password|passwd|pwd)[\s]*[:=][\s]*['"]([^'"]{4,})['"]|/gi,
    severity: 'critical'
  },
  {
    name: 'AWS Access Key',
    pattern: /AKIA[0-9A-Z]{16}/g,
    severity: 'critical'
  },
  {
    name: 'AWS Secret Key',
    pattern: /aws[_-]?secret[_-]?access[_-]?key[\s]*[:=][\s]*['"]([a-zA-Z0-9/+=]{40})['"]|/gi,
    severity: 'critical'
  },
  {
    name: 'GitHub Token',
    pattern: /gh[pousr]_[0-9a-zA-Z]{36}/g,
    severity: 'critical'
  },
  {
    name: 'Generic Private Key',
    pattern: /-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----/g,
    severity: 'critical'
  },
  {
    name: 'JWT Token',
    pattern: /eyJ[a-zA-Z0-9_-]{10,}\.[a-zA-Z0-9_-]{10,}\.[a-zA-Z0-9_-]{10,}/g,
    severity: 'medium'
  },
  {
    name: 'Database Connection String',
    pattern: /(?:mysql|postgresql|mongodb|redis):\/\/[^\s'"]+:[^\s'"]+@[^\s'"]+/gi,
    severity: 'critical'
  },
  {
    name: 'Slack Token',
    pattern: /xox[baprs]-[0-9a-zA-Z]{10,}/g,
    severity: 'high'
  },
  {
    name: 'Google API Key',
    pattern: /AIza[0-9A-Za-z_-]{35}/g,
    severity: 'high'
  },
  {
    name: 'Stripe API Key',
    pattern: /(?:sk|pk)_(?:live|test)_[0-9a-zA-Z]{24,}/g,
    severity: 'critical'
  },
  {
    name: 'Twilio API Key',
    pattern: /SK[0-9a-fA-F]{32}/g,
    severity: 'high'
  },
  {
    name: 'Hardcoded IPv4 with Port',
    pattern: /\b(?:\d{1,3}\.){3}\d{1,3}:\d{2,5}\b/g,
    severity: 'low'
  },
  {
    name: 'Basic Auth in URL',
    pattern: /https?:\/\/[^:]+:[^@]+@[^\s'"]+/gi,
    severity: 'high'
  }
];

// Files and directories to exclude from scanning
const EXCLUDE_PATTERNS = [
  'node_modules',
  '.git',
  'dist',
  'build',
  '.venv',
  '__pycache__',
  '.pytest_cache',
  'coverage',
  '.next',
  'vendor',
  'target',
  'pkg',
  'wasm',
  '.cache',
  'tmp',
  'temp',
  '.npm',
  '.yarn',
  'bundle',
  'public/assets',
  'static/assets',
  '.wasm',
  '.so',
  '.dylib',
  '.dll',
  '.exe',
  '.bin',
  'playwright-report',
  'test-results',
  '.playwright'
];

// File extensions to scan
const SCANNABLE_EXTENSIONS = [
  '.js', '.mjs', '.ts', '.tsx', '.jsx',
  '.py', '.rb', '.java', '.go', '.rs',
  '.sh', '.bash', '.zsh',
  '.yaml', '.yml', '.json', '.xml',
  '.env', '.config', '.conf',
  '.php', '.c', '.cpp', '.h', '.hpp',
  '.txt', '.md', '.sql'
];

// False positive patterns (legitimate use cases)
const FALSE_POSITIVE_PATTERNS = [
  /example\.com/i,
  /localhost/i,
  /127\.0\.0\.1/,
  /0\.0\.0\.0/,
  /YOUR_API_KEY/i,
  /YOUR_SECRET/i,
  /\{\{[^}]+\}\}/,  // Template variables
  /<[^>]+>/,        // Placeholder in angle brackets
  /secrets\.[A-Z_]+/,  // GitHub Actions secrets
  /process\.env\./,    // Environment variables
  /ENV\[/,             // Environment variable access
  /\$\{[^}]+\}/        // Shell/template variables
];

class CredentialScanner {
  constructor(options = {}) {
    this.rootDir = options.rootDir || process.cwd();
    this.verbose = options.verbose || false;
    this.findings = [];
    this.scannedFiles = 0;
    this.excludePatterns = EXCLUDE_PATTERNS;
  }

  log(message) {
    if (this.verbose) {
      console.log(message);
    }
  }

  /**
   * Check if a path should be excluded from scanning
   */
  shouldExclude(filePath) {
    return this.excludePatterns.some(pattern => filePath.includes(pattern));
  }

  /**
   * Check if a file should be scanned based on extension
   */
  shouldScan(filePath) {
    return SCANNABLE_EXTENSIONS.some(ext => filePath.endsWith(ext));
  }

  /**
   * Check if a match is likely a false positive
   */
  isFalsePositive(content, match) {
    // Check if match contains common false positive patterns
    return FALSE_POSITIVE_PATTERNS.some(pattern => pattern.test(content));
  }

  /**
   * Scan a single file for secrets
   */
  async scanFile(filePath) {
    try {
      // Skip large files (> 1MB) to prevent memory issues
      const stats = fs.statSync(filePath);
      if (stats.size > 1024 * 1024) {
        this.log(`Skipping large file: ${filePath} (${stats.size} bytes)`);
        return;
      }

      const content = fs.readFileSync(filePath, 'utf8');
      const relativePath = path.relative(this.rootDir, filePath);

      this.log(`Scanning: ${relativePath}`);

      const lines = content.split('\n');

      for (const secretPattern of SECRET_PATTERNS) {
        let match;
        secretPattern.pattern.lastIndex = 0; // Reset regex state

        while ((match = secretPattern.pattern.exec(content)) !== null) {
          const matchedText = match[0];
          const lineNumber = content.substring(0, match.index).split('\n').length;
          const lineContent = lines[lineNumber - 1] || '';

          // Skip if it's a false positive
          if (this.isFalsePositive(lineContent, matchedText)) {
            continue;
          }

          // Skip if it's a comment explaining what to do
          if (/^\s*[#\/\*]/.test(lineContent) && /example|placeholder|replace|your_|test/i.test(lineContent)) {
            continue;
          }

          this.findings.push({
            file: relativePath,
            line: lineNumber,
            column: match.index - content.lastIndexOf('\n', match.index),
            type: secretPattern.name,
            severity: secretPattern.severity,
            match: matchedText,
            context: lineContent.trim()
          });
        }
      }

      this.scannedFiles++;
    } catch (error) {
      if (error.code !== 'EISDIR') {
        console.error(`Error scanning ${filePath}:`, error.message);
      }
    }
  }

  /**
   * Recursively scan directory
   */
  async scanDirectory(dirPath) {
    const entries = fs.readdirSync(dirPath, { withFileTypes: true });

    for (const entry of entries) {
      const fullPath = path.join(dirPath, entry.name);

      if (this.shouldExclude(fullPath)) {
        continue;
      }

      if (entry.isDirectory()) {
        await this.scanDirectory(fullPath);
      } else if (entry.isFile() && this.shouldScan(fullPath)) {
        await this.scanFile(fullPath);
      }
    }
  }

  /**
   * Generate a report of findings
   */
  generateReport() {
    const summary = {
      scannedFiles: this.scannedFiles,
      totalFindings: this.findings.length,
      bySeverity: {
        critical: this.findings.filter(f => f.severity === 'critical').length,
        high: this.findings.filter(f => f.severity === 'high').length,
        medium: this.findings.filter(f => f.severity === 'medium').length,
        low: this.findings.filter(f => f.severity === 'low').length
      }
    };

    return {
      summary,
      findings: this.findings,
      scanDate: new Date().toISOString()
    };
  }

  /**
   * Print formatted report to console
   */
  printReport(report = null) {
    const r = report || this.generateReport();

    console.log('\n' + '='.repeat(70));
    console.log('              CREDENTIAL SCANNER REPORT');
    console.log('='.repeat(70) + '\n');

    console.log(`Scanned ${r.summary.scannedFiles} files`);
    console.log(`Total findings: ${r.summary.totalFindings}\n`);

    console.log('By Severity:');
    console.log(`  🔴 Critical: ${r.summary.bySeverity.critical}`);
    console.log(`  🟠 High:     ${r.summary.bySeverity.high}`);
    console.log(`  🟡 Medium:   ${r.summary.bySeverity.medium}`);
    console.log(`  🟢 Low:      ${r.summary.bySeverity.low}`);
    console.log('');

    if (r.findings.length === 0) {
      console.log('✅ No hardcoded credentials detected!\n');
      return;
    }

    console.log('Findings:\n');

    // Group findings by file
    const byFile = new Map();
    r.findings.forEach(finding => {
      if (!byFile.has(finding.file)) {
        byFile.set(finding.file, []);
      }
      byFile.get(finding.file).push(finding);
    });

    let findingNum = 1;
    for (const [file, findings] of byFile.entries()) {
      console.log(`📄 ${file}`);
      
      findings.forEach(finding => {
        const severityIcon = {
          critical: '🔴',
          high: '🟠',
          medium: '🟡',
          low: '🟢'
        }[finding.severity] || '⚪';

        console.log(`   ${findingNum}. ${severityIcon} ${finding.type} [${finding.severity.toUpperCase()}]`);
        console.log(`      Line ${finding.line}: ${finding.context.substring(0, 80)}`);
        console.log('');
        findingNum++;
      });
    }

    console.log('='.repeat(70));
    console.log('\n⚠️  Review these findings and move secrets to environment variables');
    console.log('💡 Use .env files or secret management systems (AWS Secrets Manager, etc.)\n');
  }

  /**
   * Run the scan
   */
  async scan() {
    this.findings = [];
    this.scannedFiles = 0;

    console.log(`🔍 Scanning for hardcoded credentials in: ${this.rootDir}\n`);
    
    await this.scanDirectory(this.rootDir);
    
    return this.generateReport();
  }
}

// CLI interface
if (import.meta.url === `file://${process.argv[1]}`) {
  const args = process.argv.slice(2);

  if (args.includes('--help') || args.includes('-h')) {
    console.log(`
Credential Scanner - Detect hardcoded secrets in codebase

Usage:
  credential-scanner.mjs [directory] [options]

Options:
  --verbose, -v    Enable verbose output
  --json           Output results as JSON

Examples:
  credential-scanner.mjs
  credential-scanner.mjs /path/to/project --verbose
  credential-scanner.mjs . --json
`);
    process.exit(0);
  }

  const dir = args.find(arg => !arg.startsWith('-')) || process.cwd();
  const verbose = args.includes('--verbose') || args.includes('-v');
  const json = args.includes('--json');

  const scanner = new CredentialScanner({ rootDir: dir, verbose });

  scanner.scan()
    .then(report => {
      if (json) {
        console.log(JSON.stringify(report, null, 2));
      } else {
        scanner.printReport(report);
      }

      // Exit with error code if critical or high severity findings
      if (report.summary.bySeverity.critical > 0 || report.summary.bySeverity.high > 0) {
        process.exit(1);
      }
    })
    .catch(error => {
      console.error('Error during scan:', error.message);
      process.exit(1);
    });
}

export default CredentialScanner;
