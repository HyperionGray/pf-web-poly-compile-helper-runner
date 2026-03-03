#!/usr/bin/env node

/**
 * PR Analytics Tool
 *
 * Generates simple analytics from discovered PR metadata.
 */

import fs from 'fs';
import path from 'path';

class PRAnalytics {
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

    parseDays(period) {
        const p = String(period || '30d').trim().toLowerCase();
        if (p.startsWith('${')) return 30;
        const m = p.match(/^(\d+)\s*d$/);
        if (m) return parseInt(m[1], 10);
        const n = parseInt(p, 10);
        return Number.isFinite(n) ? n : 30;
    }

    buildReport(days) {
        const cutoff = Date.now() - (days * 24 * 60 * 60 * 1000);
        const recent = this.prs.filter(pr => {
            const t = Date.parse(pr.updatedAt || pr.createdAt || '');
            return Number.isFinite(t) ? t >= cutoff : true;
        });

        const byPlatform = recent.reduce((acc, pr) => {
            acc[pr.platform] = (acc[pr.platform] || 0) + 1;
            return acc;
        }, {});

        return {
            generatedAt: new Date().toISOString(),
            periodDays: days,
            totalPRs: this.prs.length,
            recentPRs: recent.length,
            byPlatform,
            stats: {
                mergeable: recent.filter(pr => pr.mergeable).length,
                conflicts: recent.filter(pr => pr.conflicts).length,
                aiReviewed: recent.filter(pr => pr.aiReviewed).length,
                approved: recent.filter(pr => pr.reviewDecision === 'APPROVED').length
            }
        };
    }

    toHtml(report) {
        const rows = Object.entries(report.byPlatform)
            .map(([k, v]) => `<tr><td>${k}</td><td>${v}</td></tr>`)
            .join('\n');

        return `<!doctype html>
<html>
  <head>
    <meta charset="utf-8" />
    <title>PR Analytics Report</title>
    <style>
      body { font-family: system-ui, -apple-system, Segoe UI, Roboto, sans-serif; margin: 24px; }
      table { border-collapse: collapse; }
      td, th { border: 1px solid #ddd; padding: 8px 10px; }
      th { background: #f5f5f5; text-align: left; }
      .muted { color: #666; }
      code { background: #f5f5f5; padding: 2px 4px; border-radius: 4px; }
    </style>
  </head>
  <body>
    <h1>PR Analytics</h1>
    <p class="muted">Generated: ${report.generatedAt} • Period: ${report.periodDays} day(s)</p>
    <h2>Summary</h2>
    <ul>
      <li>Total PRs in dataset: <b>${report.totalPRs}</b></li>
      <li>PRs updated within period: <b>${report.recentPRs}</b></li>
      <li>Mergeable: <b>${report.stats.mergeable}</b></li>
      <li>Conflicts: <b>${report.stats.conflicts}</b></li>
      <li>AI reviewed: <b>${report.stats.aiReviewed}</b></li>
      <li>Approved: <b>${report.stats.approved}</b></li>
    </ul>
    <h2>By Platform</h2>
    <table>
      <thead><tr><th>Platform</th><th>Count</th></tr></thead>
      <tbody>${rows}</tbody>
    </table>
    <p class="muted">Source: <code>${this.prDataPath}</code></p>
  </body>
</html>`;
    }

    run(period = '30d', format = 'html', output = 'pr-report.html') {
        if (this.prs.length === 0) {
            console.log('❌ No PR data found. Run "pf pr-discover" first.');
            return;
        }

        const days = this.parseDays(period);
        const report = this.buildReport(days);
        const fmt = String(format || 'html').trim().toLowerCase();

        if (fmt === 'json') {
            console.log(JSON.stringify(report, null, 2));
            return;
        }

        const outPath = path.isAbsolute(output) ? output : path.join(process.cwd(), output);
        const html = this.toHtml(report);
        fs.writeFileSync(outPath, html);
        console.log(`✅ Report written to ${outPath}`);
    }
}

function main() {
    const args = process.argv.slice(2);
    const period = args[0] || '30d';
    const format = args[1] || 'html';
    const output = args[2] || 'pr-report.html';

    const tool = new PRAnalytics();
    tool.run(period, format, output);
}

if (import.meta.url === `file://${process.argv[1]}`) {
    main();
}

export default PRAnalytics;

