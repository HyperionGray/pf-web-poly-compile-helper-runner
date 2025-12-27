#!/usr/bin/env node
/**
 * GPT-5 Style Code Analysis Tool
 * 
 * Performs comprehensive code analysis including:
 * - Security vulnerability detection
 * - Performance optimization opportunities
 * - Architecture quality assessment
 * - Test coverage gaps
 * - Best practice compliance
 */

import fs from 'node:fs';
import path from 'node:path';
import { spawn } from 'node:child_process';
import { fileURLToPath } from 'node:url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

class CodeAnalyzer {
  constructor(options = {}) {
    this.rootDir = options.rootDir || process.cwd();
    this.verbose = options.verbose || false;
    this.results = {
      security: [],
      performance: [],
      architecture: [],
      testing: [],
      documentation: [],
      statistics: {}
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
        stdio: ['pipe', 'pipe', 'pipe'],
        shell: true
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
        resolve({ code, stdout, stderr });
      });

      child.on('error', (error) => {
        reject(error);
      });
    });
  }

  /**
   * Collect repository statistics
   */
  async collectStatistics() {
    this.log('Collecting repository statistics...');
    
    const stats = {
      python: 0,
      javascript: 0,
      typescript: 0,
      go: 0,
      java: 0,
      rust: 0,
      c: 0,
      cpp: 0,
      totalLines: 0
    };

    try {
      // Count Python files
      const pythonResult = await this.executeCommand('bash', ['-c', 'find . -name "*.py" ! -path "*/.venv/*" ! -path "*/node_modules/*" | wc -l']);
      stats.python = parseInt(pythonResult.stdout.trim()) || 0;

      // Count JavaScript files
      const jsResult = await this.executeCommand('bash', ['-c', 'find . \\( -name "*.js" -o -name "*.mjs" \\) ! -path "*/node_modules/*" ! -path "*/dist/*" | wc -l']);
      stats.javascript = parseInt(jsResult.stdout.trim()) || 0;

      // Count TypeScript files
      const tsResult = await this.executeCommand('bash', ['-c', 'find . -name "*.ts" ! -path "*/node_modules/*" ! -path "*/dist/*" | wc -l']);
      stats.typescript = parseInt(tsResult.stdout.trim()) || 0;

      // Count Go files
      const goResult = await this.executeCommand('bash', ['-c', 'find . -name "*.go" ! -path "*/vendor/*" | wc -l']);
      stats.go = parseInt(goResult.stdout.trim()) || 0;

      // Count total lines of code
      const locResult = await this.executeCommand('bash', ['-c', 'find . -type f \\( -name "*.py" -o -name "*.js" -o -name "*.mjs" -o -name "*.ts" -o -name "*.go" -o -name "*.rs" -o -name "*.c" -o -name "*.cpp" \\) ! -path "*/node_modules/*" ! -path "*/.venv/*" ! -path "*/dist/*" 2>/dev/null | xargs wc -l 2>/dev/null | tail -1']);
      
      const locMatch = locResult.stdout.match(/(\d+)/);
      stats.totalLines = locMatch ? parseInt(locMatch[1]) : 0;

    } catch (error) {
      this.log(`Error collecting statistics: ${error.message}`);
    }

    this.results.statistics = stats;
    return stats;
  }

  /**
   * Analyze security vulnerabilities
   */
  async analyzeSecurityVulnerabilities() {
    this.log('Analyzing security vulnerabilities...');
    
    const findings = [];

    try {
      // Check for hardcoded secrets using credential scanner
      const credScannerPath = path.join(this.rootDir, 'tools/security/credential-scanner.mjs');
      if (fs.existsSync(credScannerPath)) {
        this.log('Running credential scanner...');
        try {
          const result = await this.executeCommand('node', [credScannerPath, '.']);
          
          if (result.stdout.includes('found') || result.stdout.includes('detected')) {
            findings.push({
              category: 'Security',
              severity: 'critical',
              title: 'Potential Hardcoded Secrets Detected',
              description: 'Credential scanner detected potential hardcoded secrets in the codebase.',
              recommendation: 'Review the credential scanner output and move all secrets to environment variables or secure secret management.',
              file: 'Multiple files',
              cve: null
            });
          }
        } catch (err) {
          this.log(`Credential scanner error: ${err.message}`);
        }
      }

      // Check for dependency vulnerabilities
      const depCheckerPath = path.join(this.rootDir, 'tools/security/dependency-checker.mjs');
      if (fs.existsSync(depCheckerPath)) {
        this.log('Running dependency checker...');
        try {
          const result = await this.executeCommand('node', [depCheckerPath]);
          
          if (result.stdout.includes('vulnerabilities') && !result.stdout.includes('0 vulnerabilities')) {
            findings.push({
              category: 'Security',
              severity: 'high',
              title: 'Dependency Vulnerabilities Found',
              description: 'One or more dependencies have known security vulnerabilities.',
              recommendation: 'Run npm audit fix or update affected dependencies to patched versions.',
              file: 'package.json, requirements.txt',
              cve: 'See dependency checker output'
            });
          }
        } catch (err) {
          this.log(`Dependency checker error: ${err.message}`);
        }
      }

      // Check for common Python security issues
      const pythonFiles = await this.findFiles('*.py', ['*/.venv/*', '*/node_modules/*']);
      for (const file of pythonFiles.slice(0, 20)) { // Sample first 20 files
        try {
          const content = fs.readFileSync(path.join(this.rootDir, file), 'utf-8');
          
          // Check for eval/exec usage
          if (content.match(/\beval\s*\(/i) || content.match(/\bexec\s*\(/i)) {
            findings.push({
              category: 'Security',
              severity: 'high',
              title: 'Dangerous Function Usage: eval/exec',
              description: `File ${file} uses eval() or exec() which can lead to code injection vulnerabilities.`,
              recommendation: 'Replace eval/exec with safer alternatives. Use ast.literal_eval for safe evaluation of literals.',
              file: file,
              cve: 'CWE-95: Improper Neutralization of Directives in Dynamically Evaluated Code'
            });
          }

          // Check for pickle usage
          if (content.match(/import\s+pickle/) || content.match(/from\s+pickle\s+import/)) {
            findings.push({
              category: 'Security',
              severity: 'medium',
              title: 'Insecure Deserialization: pickle',
              description: `File ${file} uses pickle which can execute arbitrary code during deserialization.`,
              recommendation: 'Use JSON or other safe serialization formats. If pickle is necessary, only unpickle data from trusted sources.',
              file: file,
              cve: 'CWE-502: Deserialization of Untrusted Data'
            });
          }

          // Check for shell=True in subprocess
          if (content.match(/subprocess\.[a-z_]+\([^)]*shell\s*=\s*True/i)) {
            findings.push({
              category: 'Security',
              severity: 'high',
              title: 'Command Injection Risk: shell=True',
              description: `File ${file} uses subprocess with shell=True which can lead to command injection.`,
              recommendation: 'Use subprocess without shell=True and pass arguments as a list. Use shlex.quote() for user inputs.',
              file: file,
              cve: 'CWE-78: OS Command Injection'
            });
          }
        } catch (err) {
          this.log(`Error reading file ${file}: ${err.message}`);
        }
      }

      // Check JavaScript/TypeScript files for security issues
      const jsFiles = await this.findFiles('*.{js,mjs,ts}', ['*/node_modules/*', '*/dist/*']);
      for (const file of jsFiles.slice(0, 20)) { // Sample first 20 files
        try {
          const content = fs.readFileSync(path.join(this.rootDir, file), 'utf-8');
          
          // Check for eval usage
          if (content.match(/\beval\s*\(/)) {
            findings.push({
              category: 'Security',
              severity: 'high',
              title: 'Dangerous Function Usage: eval',
              description: `File ${file} uses eval() which can lead to code injection vulnerabilities.`,
              recommendation: 'Replace eval() with safer alternatives like JSON.parse() or Function constructor with strict validation.',
              file: file,
              cve: 'CWE-95: Improper Neutralization of Directives in Dynamically Evaluated Code'
            });
          }

          // Check for innerHTML usage
          if (content.match(/\.innerHTML\s*=/)) {
            findings.push({
              category: 'Security',
              severity: 'medium',
              title: 'XSS Risk: innerHTML Usage',
              description: `File ${file} uses innerHTML which can lead to XSS vulnerabilities if not properly sanitized.`,
              recommendation: 'Use textContent for plain text, or properly sanitize HTML with DOMPurify before using innerHTML.',
              file: file,
              cve: 'CWE-79: Cross-site Scripting (XSS)'
            });
          }
        } catch (err) {
          this.log(`Error reading file ${file}: ${err.message}`);
        }
      }

    } catch (error) {
      this.log(`Error analyzing security: ${error.message}`);
    }

    this.results.security = findings;
    return findings;
  }

  /**
   * Analyze performance optimization opportunities
   */
  async analyzePerformance() {
    this.log('Analyzing performance optimization opportunities...');
    
    const findings = [];

    try {
      // Check Python files for performance issues
      const pythonFiles = await this.findFiles('*.py', ['*/.venv/*', '*/node_modules/*']);
      for (const file of pythonFiles.slice(0, 15)) {
        try {
          const content = fs.readFileSync(path.join(this.rootDir, file), 'utf-8');
          
          // Check for list comprehension opportunities
          const loopPattern = /for\s+\w+\s+in\s+.*:\s*\n\s+\w+\.append\(/;
          if (content.match(loopPattern)) {
            findings.push({
              category: 'Performance',
              severity: 'low',
              title: 'List Comprehension Opportunity',
              description: `File ${file} has loops that could be replaced with list comprehensions for better performance.`,
              recommendation: 'Replace simple append loops with list comprehensions: result = [item for item in iterable]',
              file: file
            });
            break; // Only report once
          }
        } catch (err) {
          this.log(`Error reading file ${file}: ${err.message}`);
        }
      }

      // Check JavaScript files for performance issues
      const jsFiles = await this.findFiles('*.{js,mjs}', ['*/node_modules/*', '*/dist/*']);
      for (const file of jsFiles.slice(0, 15)) {
        try {
          const content = fs.readFileSync(path.join(this.rootDir, file), 'utf-8');
          
          // Check for synchronous file operations
          if (content.match(/fs\.(readFileSync|writeFileSync|existsSync)/)) {
            findings.push({
              category: 'Performance',
              severity: 'medium',
              title: 'Synchronous File Operations',
              description: `File ${file} uses synchronous file operations which block the event loop.`,
              recommendation: 'Use async/await with fs.promises for non-blocking file operations.',
              file: file
            });
            break; // Only report once
          }
        } catch (err) {
          this.log(`Error reading file ${file}: ${err.message}`);
        }
      }

    } catch (error) {
      this.log(`Error analyzing performance: ${error.message}`);
    }

    this.results.performance = findings;
    return findings;
  }

  /**
   * Analyze architecture quality
   */
  async analyzeArchitecture() {
    this.log('Analyzing architecture quality...');
    
    const findings = [];

    try {
      // Check for large files (potential SRP violations)
      const allFiles = await this.findFiles('*.{py,js,mjs,ts}', ['*/node_modules/*', '*/.venv/*', '*/dist/*']);
      let largeFileCount = 0;
      
      for (const file of allFiles.slice(0, 30)) {
        try {
          const content = fs.readFileSync(path.join(this.rootDir, file), 'utf-8');
          const lines = content.split('\n').length;
          
          if (lines > 500) {
            largeFileCount++;
            if (largeFileCount === 1) {
              findings.push({
                category: 'Architecture',
                severity: 'medium',
                title: 'Large Files - Potential SRP Violation',
                description: `Found ${largeFileCount} files with over 500 lines. Example: ${file} has ${lines} lines.`,
                recommendation: 'Consider breaking large files into smaller, focused modules following Single Responsibility Principle.',
                file: file
              });
            }
          }
        } catch (err) {
          this.log(`Error reading file ${file}: ${err.message}`);
        }
      }

      // Check Python files for too many imports (high coupling)
      const pythonFiles = await this.findFiles('*.py', ['*/.venv/*', '*/node_modules/*']);
      for (const file of pythonFiles.slice(0, 15)) {
        try {
          const content = fs.readFileSync(path.join(this.rootDir, file), 'utf-8');
          
          const importLines = content.split('\n').filter(line => 
            line.trim().match(/^(import|from)\s+/)
          );
          
          if (importLines.length > 20) {
            findings.push({
              category: 'Architecture',
              severity: 'low',
              title: 'High Coupling - Many Dependencies',
              description: `File ${file} imports ${importLines.length} modules, indicating high coupling.`,
              recommendation: 'Consider refactoring to reduce dependencies. Use dependency injection and interfaces.',
              file: file
            });
            break; // Only report once
          }
        } catch (err) {
          this.log(`Error reading file ${file}: ${err.message}`);
        }
      }

    } catch (error) {
      this.log(`Error analyzing architecture: ${error.message}`);
    }

    this.results.architecture = findings;
    return findings;
  }

  /**
   * Analyze test coverage
   */
  async analyzeTestCoverage() {
    this.log('Analyzing test coverage...');
    
    const findings = [];

    try {
      // Find source files
      const sourceFiles = await this.findFiles('*.{py,js,mjs,ts}', [
        '*/node_modules/*',
        '*/.venv/*',
        '**/test*/**',
        '**/*.test.*',
        '**/*.spec.*'
      ]);

      // Find test files
      const testResult = await this.executeCommand('bash', ['-c', 'find . \\( -name "*.test.*" -o -name "*.spec.*" \\) ! -path "*/node_modules/*" ! -path "*/.venv/*" | wc -l']);
      const testCount = parseInt(testResult.stdout.trim()) || 0;

      const sourceCount = sourceFiles.length;
      const ratio = sourceCount > 0 ? (testCount / sourceCount * 100).toFixed(1) : 0;

      if (ratio < 30 && sourceCount > 5) {
        findings.push({
          category: 'Testing',
          severity: 'high',
          title: 'Low Test Coverage',
          description: `Only ${ratio}% test-to-source file ratio. Found ${testCount} test files for ${sourceCount} source files.`,
          recommendation: 'Increase test coverage. Aim for at least 80% code coverage. Focus on critical paths and business logic first.',
          file: 'N/A'
        });
      }

      // Check for test configuration files
      const hasPlaywright = fs.existsSync(path.join(this.rootDir, 'playwright.config.ts')) ||
                            fs.existsSync(path.join(this.rootDir, 'playwright.config.js'));
      
      if (hasPlaywright) {
        findings.push({
          category: 'Testing',
          severity: 'info',
          title: 'Playwright Test Framework Configured',
          description: 'Project uses Playwright for end-to-end testing.',
          recommendation: 'Continue maintaining E2E tests and ensure they cover critical user workflows.',
          file: 'playwright.config.ts'
        });
      }

    } catch (error) {
      this.log(`Error analyzing test coverage: ${error.message}`);
    }

    this.results.testing = findings;
    return findings;
  }

  /**
   * Analyze documentation quality
   */
  async analyzeDocumentation() {
    this.log('Analyzing documentation quality...');
    
    const findings = [];

    try {
      // Check for README
      const hasReadme = fs.existsSync(path.join(this.rootDir, 'README.md'));
      if (!hasReadme) {
        findings.push({
          category: 'Documentation',
          severity: 'high',
          title: 'Missing README',
          description: 'Project lacks a README.md file.',
          recommendation: 'Create a README.md with project description, installation, usage, and contribution guidelines.',
          file: 'README.md'
        });
      }

      // Check for CONTRIBUTING guide
      const hasContributing = fs.existsSync(path.join(this.rootDir, 'CONTRIBUTING.md')) ||
                              fs.existsSync(path.join(this.rootDir, 'docs/development/CONTRIBUTING.md'));
      
      if (hasContributing) {
        findings.push({
          category: 'Documentation',
          severity: 'info',
          title: 'Contributing Guidelines Present',
          description: 'Project has CONTRIBUTING documentation.',
          recommendation: 'Keep contribution guidelines up to date with current development practices.',
          file: 'CONTRIBUTING.md'
        });
      }

      // Check for documentation directory
      const hasDocs = fs.existsSync(path.join(this.rootDir, 'docs'));
      
      if (hasDocs) {
        findings.push({
          category: 'Documentation',
          severity: 'info',
          title: 'Documentation Directory Present',
          description: 'Project has a dedicated documentation directory.',
          recommendation: 'Ensure all documentation is kept up to date with code changes.',
          file: 'docs/'
        });
      }

    } catch (error) {
      this.log(`Error analyzing documentation: ${error.message}`);
    }

    this.results.documentation = findings;
    return findings;
  }

  /**
   * Find files matching pattern
   */
  async findFiles(pattern, excludePatterns = []) {
    try {
      // Build exclude conditions
      let excludeCmd = '';
      for (const exclude of excludePatterns) {
        const excludePath = exclude.replace(/\*\*/g, '*').replace(/\*/g, '*');
        excludeCmd += ` ! -path "${excludePath}"`;
      }

      // Handle extension patterns like *.{js,mjs,ts}
      let namePattern = pattern;
      if (pattern.includes('{')) {
        // Convert {js,mjs,ts} to multiple -name conditions
        const match = pattern.match(/\*\.{([^}]+)}/);
        if (match) {
          const extensions = match[1].split(',');
          const conditions = extensions.map(ext => `-name "*.${ext}"`).join(' -o ');
          namePattern = `\\( ${conditions} \\)`;
        }
      } else {
        namePattern = `-name "${pattern}"`;
      }

      const cmd = `find . -type f ${namePattern}${excludeCmd}`;
      const result = await this.executeCommand('bash', ['-c', cmd]);
      
      const files = result.stdout
        .split('\n')
        .filter(f => f.trim())
        .map(f => f.replace(/^\.\//, ''));

      return files;
    } catch (error) {
      this.log(`Error finding files: ${error.message}`);
      return [];
    }
  }

  /**
   * Run comprehensive analysis
   */
  async runAnalysis() {
    console.log('🔍 Starting GPT-5 Style Code Analysis...\n');

    await this.collectStatistics();
    await this.analyzeSecurityVulnerabilities();
    await this.analyzePerformance();
    await this.analyzeArchitecture();
    await this.analyzeTestCoverage();
    await this.analyzeDocumentation();

    return this.results;
  }

  /**
   * Generate markdown report
   */
  generateReport() {
    let report = '# GPT-5 Advanced Code Analysis Report\n\n';
    
    // Statistics
    report += '## Repository Statistics\n\n';
    const stats = this.results.statistics;
    report += `- Python files: ${stats.python}\n`;
    report += `- JavaScript files: ${stats.javascript}\n`;
    report += `- TypeScript files: ${stats.typescript}\n`;
    report += `- Go files: ${stats.go}\n`;
    report += `- Total lines of code: ${stats.totalLines}\n\n`;

    // Security findings
    report += '## 🔒 Security Analysis\n\n';
    if (this.results.security.length === 0) {
      report += '✅ No high-priority security issues found.\n\n';
    } else {
      report += `Found ${this.results.security.length} security findings:\n\n`;
      for (const finding of this.results.security) {
        report += `### ${finding.severity.toUpperCase()}: ${finding.title}\n\n`;
        report += `**Description:** ${finding.description}\n\n`;
        report += `**File:** \`${finding.file}\`\n\n`;
        if (finding.cve) {
          report += `**Reference:** ${finding.cve}\n\n`;
        }
        report += `**Recommendation:** ${finding.recommendation}\n\n`;
        report += '---\n\n';
      }
    }

    // Performance findings
    report += '## ⚡ Performance Optimization Opportunities\n\n';
    if (this.results.performance.length === 0) {
      report += '✅ No major performance issues found.\n\n';
    } else {
      report += `Found ${this.results.performance.length} optimization opportunities:\n\n`;
      for (const finding of this.results.performance) {
        report += `### ${finding.title}\n\n`;
        report += `**Description:** ${finding.description}\n\n`;
        report += `**File:** \`${finding.file}\`\n\n`;
        report += `**Recommendation:** ${finding.recommendation}\n\n`;
        report += '---\n\n';
      }
    }

    // Architecture findings
    report += '## 🏗️ Architecture Quality Assessment\n\n';
    if (this.results.architecture.length === 0) {
      report += '✅ Architecture follows good practices.\n\n';
    } else {
      report += `Found ${this.results.architecture.length} architecture recommendations:\n\n`;
      for (const finding of this.results.architecture) {
        report += `### ${finding.title}\n\n`;
        report += `**Description:** ${finding.description}\n\n`;
        report += `**File:** \`${finding.file}\`\n\n`;
        report += `**Recommendation:** ${finding.recommendation}\n\n`;
        report += '---\n\n';
      }
    }

    // Testing findings
    report += '## 🧪 Test Coverage Analysis\n\n';
    if (this.results.testing.length === 0) {
      report += '✅ Test coverage is adequate.\n\n';
    } else {
      for (const finding of this.results.testing) {
        const emoji = finding.severity === 'info' ? '✅' : '⚠️';
        report += `${emoji} **${finding.title}**\n\n`;
        report += `${finding.description}\n\n`;
        report += `*Recommendation:* ${finding.recommendation}\n\n`;
        report += '---\n\n';
      }
    }

    // Documentation findings
    report += '## 📚 Documentation Quality\n\n';
    if (this.results.documentation.length === 0) {
      report += '✅ Documentation is comprehensive.\n\n';
    } else {
      for (const finding of this.results.documentation) {
        const emoji = finding.severity === 'info' ? '✅' : '📝';
        report += `${emoji} **${finding.title}**\n\n`;
        report += `${finding.description}\n\n`;
        report += `*Recommendation:* ${finding.recommendation}\n\n`;
        report += '---\n\n';
      }
    }

    // Action items
    report += '## ✅ Action Items\n\n';
    report += 'Based on the analysis above:\n\n';
    
    const highPrioritySecurity = this.results.security.filter(f => 
      f.severity === 'critical' || f.severity === 'high'
    ).length;
    
    if (highPrioritySecurity > 0) {
      report += `- [ ] Address ${highPrioritySecurity} high-priority security findings\n`;
    }
    if (this.results.performance.length > 0) {
      report += `- [ ] Implement ${this.results.performance.length} suggested performance optimizations\n`;
    }
    if (this.results.architecture.length > 0) {
      report += `- [ ] Refactor code based on ${this.results.architecture.length} architecture recommendations\n`;
    }
    
    const testingIssues = this.results.testing.filter(f => f.severity !== 'info').length;
    if (testingIssues > 0) {
      report += `- [ ] Address ${testingIssues} test coverage gaps\n`;
    }
    
    const docIssues = this.results.documentation.filter(f => f.severity !== 'info').length;
    if (docIssues > 0) {
      report += `- [ ] Update documentation (${docIssues} recommendations)\n`;
    }

    if (highPrioritySecurity === 0 && this.results.performance.length === 0 && 
        this.results.architecture.length === 0 && testingIssues === 0 && docIssues === 0) {
      report += '✅ No action items required. Code quality is excellent!\n';
    }
    
    report += '\n---\n';
    report += '*This report was automatically generated using advanced static analysis techniques.*\n';

    return report;
  }
}

// CLI execution
if (import.meta.url === `file://${process.argv[1]}`) {
  const analyzer = new CodeAnalyzer({
    rootDir: process.argv[2] || process.cwd(),
    verbose: process.argv.includes('--verbose') || process.argv.includes('-v')
  });

  try {
    await analyzer.runAnalysis();
    const report = analyzer.generateReport();
    
    // Write to file if specified
    if (process.argv.includes('--output')) {
      const outputIndex = process.argv.indexOf('--output');
      const outputFile = process.argv[outputIndex + 1];
      fs.writeFileSync(outputFile, report);
      console.log(`\n✅ Report written to ${outputFile}`);
    } else {
      console.log(report);
    }

    // Exit with error code if critical issues found
    const criticalIssues = analyzer.results.security.filter(f => 
      f.severity === 'critical' || f.severity === 'high'
    ).length;
    
    process.exit(criticalIssues > 0 ? 1 : 0);
  } catch (error) {
    console.error('❌ Analysis failed:', error.message);
    if (analyzer.verbose) {
      console.error(error.stack);
    }
    process.exit(1);
  }
}

export default CodeAnalyzer;
