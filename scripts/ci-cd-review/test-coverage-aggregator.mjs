#!/usr/bin/env node

/**
 * Test Coverage Aggregator for CI/CD Review
 * CLI wrapper; implementation lives in scripts/ci-cd-review/lib/test-coverage-aggregator.mjs
 */

import path from 'path';
import { fileURLToPath } from 'url';
import TestCoverageAggregator from './lib/test-coverage-aggregator.mjs';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// CLI usage
if (import.meta.url === `file://${process.argv[1]}`) {
  const aggregator = new TestCoverageAggregator(path.resolve(__dirname, '../..'));
  console.log('🧪 Aggregating test coverage...');

  try {
    const results = await aggregator.aggregateTestCoverage();
    const report = aggregator.generateReport(results);

    if (process.argv.includes('--json')) console.log(JSON.stringify(report, null, 2));
    else if (process.argv.includes('--cicd')) console.log(aggregator.formatForCICD(results));
    else {
      console.log('\n📊 Test Coverage Summary:');
      console.log(`Suites: ${report.summary.successfulSuites}/${report.summary.totalTestSuites} passing`);
      console.log(`Tests: ${report.summary.totalPassed}/${report.summary.totalTests} passing (${report.summary.coveragePercentage}%)`);
    }
  } catch (error) {
    console.error('❌ Error during test coverage aggregation:', error.message);
    process.exit(1);
  }
}

export default TestCoverageAggregator;
