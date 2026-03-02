#!/usr/bin/env node
/**
 * TUI Test Runner
 * 
 * Runs all TUI tests and generates comprehensive reports
 */

import { gitCleanupTests } from './git-cleanup.test.mjs';
import { writeFileSync } from 'node:fs';
import { join } from 'node:path';

async function runAllTUITests() {
  console.log('🚀 Starting TUI Test Suite Execution');
  console.log('=====================================\n');
  
  const testSuites = [
    gitCleanupTests
  ];
  
  const results = {
    suites: [],
    totalPassed: 0,
    totalFailed: 0,
    totalTests: 0,
    startTime: Date.now()
  };
  
  for (const suite of testSuites) {
    try {
      const suiteResult = await suite.run();
      results.suites.push({
        name: suite.name,
        ...suiteResult
      });
      results.totalPassed += suiteResult.passed;
      results.totalFailed += suiteResult.failed;
      results.totalTests += suiteResult.total;
    } catch (error) {
      console.error(`❌ Test suite "${suite.name}" failed to run:`, error.message);
      results.suites.push({
        name: suite.name,
        passed: 0,
        failed: 1,
        total: 1,
        error: error.message
      });
      results.totalFailed += 1;
      results.totalTests += 1;
    }
  }
  
  results.endTime = Date.now();
  results.duration = results.endTime - results.startTime;
  
  // Generate summary report
  generateSummaryReport(results);
  
  // Generate detailed report
  generateDetailedReport(results);
  
  return results;
}

function generateSummaryReport(results) {
  console.log('\n📊 TUI Test Execution Summary');
  console.log('==============================');
  console.log(`Total Tests: ${results.totalTests}`);
  console.log(`Passed: ${results.totalPassed} ✅`);
  console.log(`Failed: ${results.totalFailed} ❌`);
  console.log(`Success Rate: ${((results.totalPassed / results.totalTests) * 100).toFixed(1)}%`);
  console.log(`Duration: ${(results.duration / 1000).toFixed(2)}s`);
  
  console.log('\n📋 Suite Breakdown:');
  results.suites.forEach(suite => {
    const status = suite.failed === 0 ? '✅' : '❌';
    console.log(`  ${status} ${suite.name}: ${suite.passed}/${suite.total} passed`);
  });
}

function generateDetailedReport(results) {
  const report = {
    summary: {
      totalTests: results.totalTests,
      totalPassed: results.totalPassed,
      totalFailed: results.totalFailed,
      successRate: (results.totalPassed / results.totalTests) * 100,
      duration: results.duration,
      timestamp: new Date().toISOString()
    },
    suites: results.suites,
    environment: {
      nodeVersion: process.version,
      platform: process.platform,
      arch: process.arch,
      cwd: process.cwd()
    }
  };
  
  const reportPath = join(process.cwd(), 'tui-test-report.json');
  writeFileSync(reportPath, JSON.stringify(report, null, 2));
  console.log(`\n📄 Detailed report saved to: ${reportPath}`);
}

// Run tests if this file is executed directly
if (import.meta.url === `file://${process.argv[1]}`) {
  runAllTUITests().then(results => {
    process.exit(results.totalFailed > 0 ? 1 : 0);
  }).catch(error => {
    console.error('TUI test execution failed:', error);
    process.exit(1);
  });
}

export { runAllTUITests };