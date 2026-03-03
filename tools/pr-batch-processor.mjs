#!/usr/bin/env node

/**
 * PR Batch Processor
 *
 * Orchestrates multi-PR processing (review + optional merge).
 * This implementation is intentionally conservative: it can dry-run safely.
 */

import fs from 'fs';
import path from 'path';
import AIReviewer from './pr-ai-review.mjs';

class PRBatchProcessor {
    constructor() {
        this.prDataPath = path.join(process.env.HOME, '.config', 'pf', 'discovered-prs.json');
        this.prs = this.loadPRs();
        this.reviewer = new AIReviewer();
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
        if (v.startsWith('${')) return defaultValue;
        return ['1', 'true', 'yes', 'y', 'on'].includes(v);
    }

    parseIntValue(value, defaultValue) {
        if (value === undefined || value === null) return defaultValue;
        const v = String(value).trim();
        if (v.startsWith('${')) return defaultValue;
        const n = parseInt(v, 10);
        return Number.isFinite(n) ? n : defaultValue;
    }

    filterPRs(filter) {
        const f = (filter || 'ready').toString().trim().toLowerCase();

        if (f === 'all') return this.prs;
        if (f === 'open') return this.prs.filter(pr => pr.state === 'open');
        if (f === 'ready' || f === 'ready-to-merge') {
            return this.prs.filter(pr =>
                pr.state === 'open' &&
                pr.mergeable &&
                !pr.conflicts &&
                (pr.reviewDecision === 'APPROVED' || pr.aiReviewed) &&
                (pr.statusChecks === 'SUCCESS' || pr.statusChecks === 'PENDING' || pr.statusChecks === 'unknown')
            );
        }

        return this.prs;
    }

    async process(filter = 'ready', maxConcurrent = 5, dryRun = false) {
        console.log('🧰 Starting PR batch processing...\n');

        if (this.prs.length === 0) {
            console.log('❌ No PR data found. Run "pf pr-discover" first.');
            return;
        }

        const prs = this.filterPRs(filter);
        console.log(`📊 Filter: ${filter}`);
        console.log(`📌 Candidates: ${prs.length}`);
        console.log(`🧵 Max concurrent: ${maxConcurrent}`);
        console.log(`🧪 Dry run: ${dryRun ? 'true' : 'false'}`);
        console.log('');

        if (prs.length === 0) {
            console.log('✅ Nothing to do.');
            return;
        }

        if (dryRun) {
            prs.forEach(pr => {
                console.log(`- Would review: ${pr.platform} ${pr.repository}#${pr.id} (${pr.title})`);
            });
            console.log('');
            console.log('ℹ️  This tool currently automates AI review only.');
            console.log('    For merges, use: pf pr-merge-safe pr_id=<id> or pf pr-merge-all');
            return;
        }

        // Minimal automation: run AI review for each PR that is not yet AI reviewed.
        const queue = prs.filter(pr => !pr.aiReviewed);
        if (queue.length === 0) {
            console.log('✅ All candidate PRs already have AI reviews.');
            return;
        }

        console.log(`🤖 Running AI reviews for ${queue.length} PR(s)...\n`);

        const concurrency = Math.max(1, maxConcurrent);
        let idx = 0;

        const worker = async () => {
            while (idx < queue.length) {
                const current = queue[idx++];
                try {
                    await this.reviewer.reviewPR(current.id);
                } catch (error) {
                    console.error(`❌ Failed review for PR #${current.id}: ${error.message}`);
                }
            }
        };

        await Promise.all(Array.from({ length: concurrency }, () => worker()));

        console.log('\n✅ Batch processing complete.');
        console.log('Next: pf pr-list (to see updated AI review state)');
    }
}

async function main() {
    const args = process.argv.slice(2);
    const filter = args[0] || 'ready';
    const maxConcurrent = args[1] || '5';
    const dryRun = args[2] || 'false';

    const processor = new PRBatchProcessor();
    await processor.process(filter, processor.parseIntValue(maxConcurrent, 5), processor.parseBool(dryRun, false));
}

if (import.meta.url === `file://${process.argv[1]}`) {
    main().catch(console.error);
}

export default PRBatchProcessor;

