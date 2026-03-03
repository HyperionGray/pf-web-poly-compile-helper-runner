#!/usr/bin/env node

/**
 * PR Conflict Resolver Tool (AI-assisted)
 * 
 * This is a lightweight companion to `pr-conflict-detector.mjs`.
 * It focuses on producing actionable guidance and optionally generating
 * a suggested resolution plan, without making destructive changes by default.
 */

import fs from 'fs';
import path from 'path';

class PRConflictResolver {
    constructor() {
        this.prDataPath = path.join(process.env.HOME, '.config', 'pf', 'discovered-prs.json');
        this.analysisDir = path.join(process.env.HOME, '.config', 'pf', 'conflict-analysis');
        this.prs = this.loadPRs();
    }

    loadPRs() {
        try {
            if (fs.existsSync(this.prDataPath)) {
                return JSON.parse(fs.readFileSync(this.prDataPath, 'utf8'));
            }
        } catch (error) {
            console.error('❌ Failed to load PR data:', error.message);
        }

        return [];
    }

    parseBool(value, defaultValue = false) {
        if (value === undefined || value === null) return defaultValue;
        const v = String(value).trim().toLowerCase();
        if (v.startsWith('${')) return defaultValue; // tolerate pf/bash-style default placeholders
        return ['1', 'true', 'yes', 'y', 'on'].includes(v);
    }

    findLatestAnalysis() {
        try {
            if (!fs.existsSync(this.analysisDir)) return null;
            const files = fs
                .readdirSync(this.analysisDir)
                .filter(f => f.endsWith('.json'))
                .map(f => path.join(this.analysisDir, f))
                .sort((a, b) => fs.statSync(b).mtimeMs - fs.statSync(a).mtimeMs);
            return files[0] || null;
        } catch {
            return null;
        }
    }

    loadLatestAnalysis() {
        const latest = this.findLatestAnalysis();
        if (!latest) return null;
        try {
            return JSON.parse(fs.readFileSync(latest, 'utf8'));
        } catch {
            return null;
        }
    }

    resolve(prId, provider = 'openai', autoApply = false) {
        console.log(`🧩 Conflict resolver for PR #${prId}`);

        if (this.prs.length === 0) {
            console.log('❌ No PR data found. Run "pf pr-discover" first.');
            return;
        }

        const pr = this.prs.find(p => p.id.toString() === prId.toString());
        if (!pr) {
            console.log(`❌ PR #${prId} not found in discovered PRs. Run "pf pr-discover" first.`);
            return;
        }

        const analysis = this.loadLatestAnalysis();
        const conflictsForPr = analysis?.conflicts?.filter(c => c?.pr?.id?.toString() === prId.toString()) || [];

        console.log('');
        console.log(`📋 ${pr.platform.toUpperCase()} ${pr.repository}#${pr.id}`);
        console.log(`📝 ${pr.title}`);
        console.log(`👤 ${pr.author}`);
        console.log(`🔗 ${pr.url}`);
        console.log('');

        if (conflictsForPr.length > 0) {
            const conflict = conflictsForPr[0];
            const files = conflict.conflictFiles || pr.conflictFiles || [];
            console.log(`⚠️  Conflicts detected (latest analysis): ${files.length ? files.length : 'unknown'} file(s)`);
            if (files.length) {
                console.log(`📁 Files: ${files.slice(0, 10).join(', ')}${files.length > 10 ? ' ...' : ''}`);
            }
            console.log('');
        } else if (pr.conflicts) {
            console.log('⚠️  PR is marked as having conflicts.');
            console.log('');
        } else {
            console.log('✅ No conflict markers found in local metadata.');
            console.log('If the platform reports conflicts, re-run: pf pr-conflict-detect');
            console.log('');
        }

        console.log(`🤖 Provider: ${provider}${autoApply ? ' (auto-apply enabled)' : ''}`);
        console.log('');

        console.log('💡 Recommended resolution workflow:');
        if (pr.platform === 'github') {
            console.log(`  1) gh pr checkout ${pr.id} --repo ${pr.repository}`);
        } else if (pr.platform === 'gitlab') {
            console.log(`  1) glab mr checkout ${pr.id} --repo ${pr.repository}`);
        } else {
            console.log('  1) Checkout the PR branch locally (platform unknown)');
        }
        console.log('  2) git fetch --all --prune');
        console.log('  3) git merge (or rebase) onto the target branch');
        console.log('  4) Resolve conflicts, run tests, push updates');
        console.log('');

        if (autoApply) {
            console.log('⚠️  Auto-apply is requested, but this tool is intentionally conservative.');
            console.log('    It currently does not modify branches automatically.');
            console.log('    Use the workflow above, or implement auto-apply in a controlled environment.');
        } else {
            console.log('ℹ️  Tip: pass auto_apply=true to request auto-apply behavior (currently informational only).');
        }
    }
}

function main() {
    const args = process.argv.slice(2);
    const prId = args[0];
    const provider = args[1] && !args[1].startsWith('${') ? args[1] : 'openai';
    const autoApply = args[2];

    if (!prId) {
        console.log('Usage: pr-conflict-resolver.mjs <pr_id> [provider] [auto_apply]');
        console.log('Example: pr-conflict-resolver.mjs 123 openai false');
        return;
    }

    const resolver = new PRConflictResolver();
    resolver.resolve(prId, provider, resolver.parseBool(autoApply, false));
}

if (import.meta.url === `file://${process.argv[1]}`) {
    main();
}

export default PRConflictResolver;

