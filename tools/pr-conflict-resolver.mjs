#!/usr/bin/env node

/**
 * PR Conflict Resolver (safe / non-destructive)
 * Generates a conflict-resolution plan for a specified PR.
 */

import fs from 'node:fs';
import path from 'node:path';

import { ensureDir, loadPrContext, parseBool, writeJson } from './pr-common.mjs';

class ConflictResolver {
  constructor() {
    this.ctx = loadPrContext();
    this.prDataPath = this.ctx.paths.discoveredPrsFile;
    this.prs = this.loadPRs();
  }

  loadPRs() {
    try {
      if (fs.existsSync(this.prDataPath)) {
        return JSON.parse(fs.readFileSync(this.prDataPath, 'utf8'));
      }
    } catch (error) {
      console.error('❌ Failed to load PR data:', error?.message || error);
    }
    return [];
  }

  findPR(prId) {
    const id = prId?.toString?.() ?? `${prId}`;
    return this.prs.find((p) => p.id?.toString?.() === id) || null;
  }

  generatePlan(pr, provider = 'openai', autoApply = false) {
    const hasConflicts = !!pr.conflicts;

    return {
      timestamp: new Date().toISOString(),
      provider,
      autoApplyRequested: autoApply,
      applied: false,
      pr: {
        id: pr.id,
        platform: pr.platform,
        repository: pr.repository,
        title: pr.title,
        url: pr.url,
        conflicts: hasConflicts,
        conflictFiles: pr.conflictFiles || [],
      },
      steps: hasConflicts
        ? [
            'Fetch the PR branch locally (gh/glab or git).',
            'Merge/rebase onto the target base branch.',
            'Resolve conflicts file-by-file, run tests, and push updates.',
            'Re-run `pf pr-conflict-detect` to confirm status.',
          ]
        : ['No conflicts flagged; re-run `pf pr-conflict-detect` if you suspect drift.'],
      notes: [
        'This tool is intentionally non-destructive.',
        'Automatic conflict resolution is not applied unless you implement provider integration and enable it explicitly.',
      ],
    };
  }

  savePlan(plan) {
    const dir = this.ctx.paths.conflictAnalysisDir;
    ensureDir(dir);
    const filename = `conflict-resolution-${plan.pr.platform}-${plan.pr.repository.replace('/', '-')}-${plan.pr.id}-${Date.now()}.json`;
    const filepath = path.join(dir, filename);
    writeJson(filepath, plan);
    return filepath;
  }
}

async function main() {
  const args = process.argv.slice(2);
  const prId = args[0];
  const provider = args[1] || 'openai';
  const autoApply = parseBool(args[2] ?? 'false', false);

  if (!prId) {
    console.error('❌ Missing PR ID');
    console.log('Usage: node tools/pr-conflict-resolver.mjs <pr_id> [provider] [auto_apply]');
    process.exitCode = 1;
    return;
  }

  const resolver = new ConflictResolver();
  const pr = resolver.findPR(prId);
  if (!pr) {
    console.error(`❌ PR #${prId} not found. Run "pf pr-discover" first.`);
    process.exitCode = 1;
    return;
  }

  if (!pr.conflicts) {
    console.log(`✅ PR #${pr.id} is not flagged as conflicted.`);
  } else {
    console.log(`⚠️  PR #${pr.id} is flagged as conflicted; generating resolution plan...`);
  }

  const plan = resolver.generatePlan(pr, provider, autoApply);
  const saved = resolver.savePlan(plan);
  console.log(`💾 Conflict resolution plan saved to ${saved}`);

  if (autoApply) {
    console.log('⚠️  auto_apply requested, but automatic application is not implemented; no changes were made.');
  }
}

if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => {
    console.error(err);
    process.exitCode = 1;
  });
}

export default ConflictResolver;

