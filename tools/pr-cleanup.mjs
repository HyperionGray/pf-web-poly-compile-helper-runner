#!/usr/bin/env node

/**
 * PR Cleanup (safe / mostly non-destructive)
 * Cleans up local PR state and optionally prunes old entries.
 */

import fs from 'node:fs';

import { loadPrContext, parseBool, writeJson } from './pr-common.mjs';

function loadPRs(filePath) {
  try {
    if (fs.existsSync(filePath)) {
      return JSON.parse(fs.readFileSync(filePath, 'utf8'));
    }
  } catch {
    // ignore
  }
  return [];
}

function isOlderThan(dateValue, days) {
  const t = new Date(dateValue || 0).getTime();
  if (!Number.isFinite(t) || t <= 0) return false;
  return t < Date.now() - days * 24 * 60 * 60 * 1000;
}

function main() {
  const args = process.argv.slice(2);
  const daysOld = parseInt(args[0] || '', 10) || 30;
  const dryRun = parseBool(args[1] ?? 'false', false);

  const ctx = loadPrContext();
  const prs = loadPRs(ctx.paths.discoveredPrsFile);
  if (prs.length === 0) {
    console.log('❌ No PR data found. Run "pf pr-discover" first.');
    return;
  }

  const mergedOld = prs.filter((p) => p.state === 'merged' && isOlderThan(p.mergedAt || p.updatedAt, daysOld));
  const staleOpen = prs.filter((p) => p.state === 'open' && isOlderThan(p.updatedAt, daysOld));

  console.log(`🧹 Cleanup (days_old=${daysOld}, dry_run=${dryRun})`);
  console.log(`- old merged entries: ${mergedOld.length}`);
  console.log(`- stale open entries: ${staleOpen.length}`);

  if (dryRun) {
    for (const pr of mergedOld.slice(0, 20)) console.log(`  - merged: ${pr.repository}#${pr.id} (${pr.title})`);
    for (const pr of staleOpen.slice(0, 20)) console.log(`  - stale: ${pr.repository}#${pr.id} (${pr.title})`);
    if (mergedOld.length + staleOpen.length > 40) console.log('  ...');
    return;
  }

  const pruned = prs.filter((p) => !(p.state === 'merged' && isOlderThan(p.mergedAt || p.updatedAt, daysOld)));
  writeJson(ctx.paths.discoveredPrsFile, pruned);
  console.log(`✅ PR state updated: ${ctx.paths.discoveredPrsFile} (removed ${prs.length - pruned.length})`);
  console.log('ℹ️  Remote branch cleanup is not performed by this script.');
}

if (import.meta.url === `file://${process.argv[1]}`) {
  main();
}

