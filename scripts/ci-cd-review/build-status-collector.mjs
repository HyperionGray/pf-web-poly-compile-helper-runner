#!/usr/bin/env node

/**
 * Build Status Collector for CI/CD Review
 * CLI wrapper; implementation lives in scripts/ci-cd-review/lib/build-status-collector.mjs
 */

import path from 'path';
import { fileURLToPath } from 'url';
import BuildStatusCollector from './lib/build-status-collector.mjs';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

if (import.meta.url === `file://${process.argv[1]}`) {
  const collector = new BuildStatusCollector(path.resolve(__dirname, '../..'));
  console.log('🔨 Collecting build status...');

  try {
    const results = await collector.collectBuildStatus();
    if (process.argv.includes('--cicd')) console.log(collector.formatForCICD(results));
    else console.log(JSON.stringify(collector.generateReport(results), null, 2));
  } catch (error) {
    console.error('❌ Error during build status collection:', error.message);
    process.exit(1);
  }
}

export default BuildStatusCollector;

