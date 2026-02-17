#!/usr/bin/env node

/**
 * PR Batch Processor
 * Orchestrates AI review + safe merge workflows.
 */

import fs from 'node:fs';

import BatchAIReviewer from './pr-ai-review-batch.mjs';
import BatchMerger from './pr-merge-batch.mjs';
import { loadPrContext, parseBool } from './pr-common.mjs';

function loadPRs(prDataPath) {
  try {
    if (fs.existsSync(prDataPath)) {
      return JSON.parse(fs.readFileSync(prDataPath, 'utf8'));
    }
  } catch {
    // ignore
  }
  return [];
}

function filterPRs(prs, filter) {
  const f = (filter || 'all').toLowerCase();
  if (f === 'ready' || f === 'ready-to-merge') {
    return prs.filter(
      (pr) =>
        pr.state === 'open' &&
        pr.mergeable &&
        !pr.conflicts &&
        pr.statusChecks !== 'FAILURE' &&
        (pr.reviewDecision === 'APPROVED' || pr.aiReviewed)
    );
  }
  if (f === 'needs-review') return prs.filter((pr) => pr.state === 'open' && !pr.reviewDecision);
  if (f === 'conflicts') return prs.filter((pr) => pr.state === 'open' && pr.conflicts);
  return prs;
}

async function main() {
  const args = process.argv.slice(2);
  const filter = args[0] || 'ready';
  const maxConcurrent = parseInt(args[1] || '', 10) || 5;
  const dryRun = parseBool(args[2] ?? 'false', false);

  const ctx = loadPrContext();
  const prs = loadPRs(ctx.paths.discoveredPrsFile);
  if (prs.length === 0) {
    console.log('❌ No PR data found. Run "pf pr-discover" first.');
    return;
  }

  const selected = filterPRs(prs, filter);
  console.log(`⚡ Batch processing filter=${filter} selected=${selected.length} dry_run=${dryRun}`);
  if (selected.length === 0) return;

  if (dryRun) {
    for (const pr of selected.slice(0, 20)) {
      console.log(`- ${pr.platform} ${pr.repository}#${pr.id}: ${pr.title}`);
    }
    if (selected.length > 20) console.log(`... (${selected.length - 20} more)`);
    return;
  }

  // Pick a default provider/model from config.
  const providers = ctx.pr.ai?.providers || {};
  const enabledProvider =
    Object.entries(providers).find(([, p]) => p && typeof p === 'object' && p.enabled)?.[0] || 'openai';
  const model = providers?.[enabledProvider]?.model || null;

  const reviewer = new BatchAIReviewer();
  await reviewer.reviewPRBatch(enabledProvider, model, maxConcurrent);

  const merger = new BatchMerger();
  await merger.batchMerge('squash', true, true, false);
}

if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => {
    console.error(err);
    process.exitCode = 1;
  });
}

