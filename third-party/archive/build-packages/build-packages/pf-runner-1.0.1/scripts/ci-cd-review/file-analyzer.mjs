#!/usr/bin/env node

/**
 * File Analyzer for CI/CD Review
 * CLI wrapper; implementation lives in scripts/ci-cd-review/lib/file-analyzer.mjs
 */

import path from 'path';
import { fileURLToPath } from 'url';
import FileAnalyzer from './lib/file-analyzer.mjs';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

if (import.meta.url === `file://${process.argv[1]}`) {
  const analyzer = new FileAnalyzer(path.resolve(__dirname, '../..'));

  console.log('🔍 Analyzing repository files...');

  try {
    const results = await analyzer.scanDirectory();
    const report = analyzer.generateReport(results);

    if (process.argv.includes('--json')) console.log(JSON.stringify(report, null, 2));
    else if (process.argv.includes('--cicd')) console.log(analyzer.formatForCICD(results));
    else {
      console.log('\n📊 File Analysis Summary:');
      console.log(`Total files scanned: ${results.totalFiles}`);
      console.log(`Total lines of code: ${report.summary.totalLines.toLocaleString()}`);
      console.log(`Large files (>500 lines): ${report.summary.largeFileCount}`);
    }
  } catch (error) {
    console.error('❌ Error during file analysis:', error.message);
    process.exit(1);
  }
}

export default FileAnalyzer;

