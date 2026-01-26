#!/usr/bin/env node

/**
 * PR Cleanup Tool
 *
 * Identifies merged / stale PRs from the discovered dataset and prints
 * recommended cleanup actions. Destructive actions are not performed by
 * default; use platform CLIs manually when ready.
 */

import fs from 'fs';
import path from 'path';

class PRCleanup {
    constructor() {
        this.prDataPath = path.join(process.env.HOME, '.config', 'pf', 'discovered-prs.json');
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
        if (v.startsWith('${')) return defaultValue;
        return ['1', 'true', 'yes', 'y', 'on'].includes(v);
    }

    parseDays(value, defaultDays = 30) {
        if (value === undefined || value === null) return defaultDays;
        const v = String(value).trim().toLowerCase();
        if (v.startsWith('${')) return defaultDays;
        const n = parseInt(v, 10);
        return Number.isFinite(n) ? n : defaultDays;
    }

    run(daysOld = 30, dryRun = false) {
        if (this.prs.length === 0) {
            console.log('❌ No PR data found. Run "pf pr-discover" first.');
            return;
        }

        const cutoff = Date.now() - (daysOld * 24 * 60 * 60 * 1000);
        const stale = this.prs.filter(pr => {
            const t = Date.parse(pr.updatedAt || pr.createdAt || '');
            return Number.isFinite(t) ? t < cutoff : false;
        });

        console.log('🧹 PR Cleanup');
        console.log(`📅 Threshold: ${daysOld} day(s)`);
        console.log(`🧪 Dry run: ${dryRun ? 'true' : 'false'}`);
        console.log('');

        console.log(`Found ${stale.length} stale PR(s):`);
        stale.slice(0, 50).forEach(pr => {
            console.log(`- ${pr.platform} ${pr.repository}#${pr.id} (${pr.state}) updated=${pr.updatedAt || pr.createdAt}`);
        });

        if (stale.length > 50) {
            console.log(`... and ${stale.length - 50} more`);
        }

        console.log('');
        if (dryRun) {
            console.log('ℹ️  Dry run only. No actions performed.');
            return;
        }

        console.log('ℹ️  This tool currently reports candidates only (no destructive actions).');
        console.log('Suggested next steps:');
        console.log('  - Delete merged branches using your platform UI/CLI');
        console.log('  - Close stale PRs after review');
    }
}

function main() {
    const args = process.argv.slice(2);
    const daysOld = args[0] || '30';
    const dryRun = args[1] || 'false';

    const tool = new PRCleanup();
    tool.run(tool.parseDays(daysOld, 30), tool.parseBool(dryRun, false));
}

if (import.meta.url === `file://${process.argv[1]}`) {
    main();
}

export default PRCleanup;

