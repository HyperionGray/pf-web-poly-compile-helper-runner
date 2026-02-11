/**
 * Test Coverage Aggregator for CI/CD Review
 * Aggregates test results from Playwright and unit tests.
 */

import fs from 'fs';
import path from 'path';
import { spawn } from 'child_process';

class TestCoverageAggregator {
  constructor(rootPath) {
    this.rootPath = rootPath;
    this.testTypes = {
      playwright: { command: 'npm', args: ['run', 'test'], description: 'Playwright E2E Tests' },
      unit: { command: 'npm', args: ['run', 'test:unit'], description: 'Unit Tests' },
      tui: { command: 'npm', args: ['run', 'test:tui'], description: 'TUI Tests' },
      grammar: { command: 'npm', args: ['run', 'test:grammar'], description: 'Grammar Tests' },
      api: { command: 'npm', args: ['run', 'test:api'], description: 'API Tests' }
    };
  }

  async runTestSuite(testType, config, { timeoutMs = 30000 } = {}) {
    return new Promise((resolve) => {
      console.log(`🧪 Running ${config.description}...`);

      const startTime = Date.now();
      const childProcess = spawn(config.command, config.args, { cwd: this.rootPath, stdio: 'pipe' });

      let stdout = '';
      let stderr = '';
      let settled = false;

      const finish = (payload) => {
        if (settled) return;
        settled = true;
        resolve({
          testType,
          description: config.description,
          duration: Date.now() - startTime,
          stdout,
          stderr,
          timestamp: new Date().toISOString(),
          ...payload
        });
      };

      childProcess.stdout.on('data', (data) => {
        stdout += data.toString();
      });
      childProcess.stderr.on('data', (data) => {
        stderr += data.toString();
      });

      childProcess.on('error', (error) => {
        finish({ exitCode: -1, success: false, error: error.message });
      });

      childProcess.on('close', (code) => {
        finish({ exitCode: code ?? -1, success: code === 0 });
      });

      const t = setTimeout(() => {
        try {
          childProcess.kill('SIGTERM');
        } catch {
          // ignore
        }
        finish({ exitCode: -1, success: false, timedOut: true, error: `Test timed out after ${Math.round(timeoutMs / 1000)} seconds` });
      }, timeoutMs);

      childProcess.on('exit', () => clearTimeout(t));
    });
  }

  parseTestResults(result) {
    const parsed = {
      testType: result.testType,
      description: result.description,
      success: result.success,
      duration: result.duration,
      timestamp: result.timestamp,
      stats: { total: 0, passed: 0, failed: 0, skipped: 0 },
      details: []
    };

    if (result.testType === 'playwright') {
      const m = result.stdout.match(/(\d+)\s+passed.*?(\d+)\s+failed.*?(\d+)\s+skipped/i);
      if (m) {
        parsed.stats.passed = parseInt(m[1], 10) || 0;
        parsed.stats.failed = parseInt(m[2], 10) || 0;
        parsed.stats.skipped = parseInt(m[3], 10) || 0;
        parsed.stats.total = parsed.stats.passed + parsed.stats.failed + parsed.stats.skipped;
      }
    }

    if (['unit', 'tui', 'grammar', 'api'].includes(result.testType)) {
      const testLines = (result.stdout || '')
        .split('\n')
        .filter((line) => line.includes('✓') || line.includes('✗') || line.includes('PASS') || line.includes('FAIL'));

      parsed.stats.total = testLines.length;
      parsed.stats.passed = testLines.filter((line) => line.includes('✓') || line.includes('PASS')).length;
      parsed.stats.failed = testLines.filter((line) => line.includes('✗') || line.includes('FAIL')).length;
    }

    if (!result.success) {
      const msg = (result.stderr || result.error || result.stdout || '').trim();
      if (msg) parsed.details.push({ type: 'error', message: msg.split('\n').slice(0, 8).join('\n') });
    }

    return parsed;
  }

  async scanTestFiles() {
    const testFiles = { playwright: [], unit: [], other: [] };

    const scanDirectory = (dirPath) => {
      if (!fs.existsSync(dirPath)) return;

      let items;
      try {
        items = fs.readdirSync(dirPath, { withFileTypes: true });
      } catch (error) {
        console.warn(`Warning: Could not scan test directory ${dirPath}: ${error.message}`);
        return;
      }

      for (const item of items) {
        const itemPath = path.join(dirPath, item.name);
        if (item.isDirectory()) {
          scanDirectory(itemPath);
          continue;
        }
        if (!item.isFile()) continue;

        const relativePath = path.relative(this.rootPath, itemPath);

        if (item.name.endsWith('.spec.ts') || item.name.endsWith('.spec.js')) testFiles.playwright.push(relativePath);
        else if (item.name.endsWith('.test.mjs') || item.name.endsWith('.test.js')) testFiles.unit.push(relativePath);
        else if (item.name.includes('test') && (item.name.endsWith('.js') || item.name.endsWith('.mjs') || item.name.endsWith('.sh'))) {
          testFiles.other.push(relativePath);
        }
      }
    };

    scanDirectory(path.join(this.rootPath, 'tests'));
    scanDirectory(path.join(this.rootPath, 'pf-runner'));
    return testFiles;
  }

  calculateSummary(results, testFiles) {
    const summary = {
      totalTestFiles: testFiles.playwright.length + testFiles.unit.length + testFiles.other.length,
      totalTestSuites: results.length,
      successfulSuites: results.filter((r) => r.success).length,
      failedSuites: results.filter((r) => !r.success).length,
      totalTests: results.reduce((sum, r) => sum + r.stats.total, 0),
      totalPassed: results.reduce((sum, r) => sum + r.stats.passed, 0),
      totalFailed: results.reduce((sum, r) => sum + r.stats.failed, 0),
      totalSkipped: results.reduce((sum, r) => sum + r.stats.skipped, 0),
      totalDuration: results.reduce((sum, r) => sum + r.duration, 0),
      coveragePercentage: 0
    };

    if (summary.totalTests > 0) summary.coveragePercentage = Math.round((summary.totalPassed / summary.totalTests) * 100);
    return summary;
  }

  async aggregateTestCoverage({ timeoutMs = 30000 } = {}) {
    console.log('🔍 Scanning test files...');
    const testFiles = await this.scanTestFiles();

    console.log('🧪 Running test suites...');
    const results = [];

    for (const [testType, config] of Object.entries(this.testTypes)) {
      const raw = await this.runTestSuite(testType, config, { timeoutMs });
      results.push(this.parseTestResults(raw));
    }

    return { testFiles, results, summary: this.calculateSummary(results, testFiles) };
  }

  generateReport(aggregationResults) {
    return {
      timestamp: new Date().toISOString(),
      summary: aggregationResults.summary,
      testFiles: aggregationResults.testFiles,
      results: aggregationResults.results,
      recommendations: this.generateRecommendations(aggregationResults)
    };
  }

  generateRecommendations(results) {
    const recommendations = [];
    const failedSuites = results.results.filter((r) => !r.success);
    if (failedSuites.length > 0) {
      recommendations.push({
        type: 'test-failures',
        priority: 'high',
        message: `${failedSuites.length} test suites are failing`,
        suites: failedSuites.map((s) => s.testType)
      });
    }
    if (results.summary.coveragePercentage < 80) {
      recommendations.push({
        type: 'test-coverage',
        priority: 'medium',
        message: `Test coverage is ${results.summary.coveragePercentage}% - consider adding more tests`,
        currentCoverage: results.summary.coveragePercentage
      });
    }
    return recommendations;
  }

  formatForCICD(aggregationResults) {
    const report = this.generateReport(aggregationResults);
    let output = '## Test Coverage and Playwright Integration\n\n';

    const overallStatus = report.summary.failedSuites === 0 ? '✅ Success' : '❌ Failed';
    output += `**Overall Test Status:** ${overallStatus}\n\n`;

    output += '### Test Suite Results:\n';
    report.results.forEach((result) => {
      const status = result.success ? '✅' : '❌';
      const duration = Math.round(result.duration / 1000);
      output += `${status} **${result.description}**: ${result.stats.passed}/${result.stats.total} tests passed (${duration}s)\n`;
    });

    output += '\n### Test Coverage Summary:\n';
    output += `- **Total Test Files**: ${report.summary.totalTestFiles}\n`;
    output += `- **Test Suites**: ${report.summary.successfulSuites}/${report.summary.totalTestSuites} passing\n`;
    output += `- **Individual Tests**: ${report.summary.totalPassed}/${report.summary.totalTests} passing (${report.summary.coveragePercentage}%)\n`;
    output += `- **Total Duration**: ${Math.round(report.summary.totalDuration / 1000)}s\n`;

    output += '\n';
    return output;
  }
}

export default TestCoverageAggregator;

