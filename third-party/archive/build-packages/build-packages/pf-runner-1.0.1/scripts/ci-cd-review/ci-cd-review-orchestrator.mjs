#!/usr/bin/env node

/**
 * CI/CD Review Orchestrator
 * CLI wrapper; implementation lives in scripts/ci-cd-review/lib/ci-cd-review-orchestrator.mjs
 */

import path from 'path';
import { fileURLToPath } from 'url';
import CICDReviewOrchestrator from './lib/ci-cd-review-orchestrator.mjs';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

function parseArgs(argv) {
  const args = { root: path.resolve(__dirname, '../..'), save: false, json: false, help: false };
  for (let i = 2; i < argv.length; i++) {
    const a = argv[i];
    if (a === '--help' || a === '-h') args.help = true;
    else if (a === '--save') args.save = true;
    else if (a === '--json') args.json = true;
    else if (a === '--root') args.root = path.resolve(argv[++i] ?? args.root);
    else if (a.startsWith('--root=')) args.root = path.resolve(a.slice('--root='.length));
  }
  return args;
}

function showHelp() {
  console.log(`CI/CD Review Orchestrator

Usage:
  node scripts/ci-cd-review/ci-cd-review-orchestrator.mjs [--root PATH] [--save] [--json] [--help]
`);
}

if (import.meta.url === `file://${process.argv[1]}`) {
  const args = parseArgs(process.argv);
  if (args.help) {
    showHelp();
    process.exit(0);
  }

  const orchestrator = new CICDReviewOrchestrator(args.root);
  try {
    const reviewResults = await orchestrator.runCompleteReview();
    const report = orchestrator.formatReviewReport(reviewResults);

    if (args.save) await orchestrator.saveReportToFile(report);
    if (args.json) console.log(JSON.stringify(reviewResults, null, 2));
    else console.log(report);

    const hasFailures = Object.values(reviewResults.components).some((component) => !component.success);
    process.exit(hasFailures ? 1 : 0);
  } catch (error) {
    console.error('❌ CI/CD Review failed:', error.message);
    process.exit(1);
  }
}

export default CICDReviewOrchestrator;

