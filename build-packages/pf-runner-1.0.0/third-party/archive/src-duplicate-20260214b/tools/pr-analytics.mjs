#!/usr/bin/env node

/**
 * PR Analytics
 * Generates basic metrics from discovered PRs and writes json/html reports.
 */

import fs from 'node:fs';
import path from 'node:path';

import { ensureDir, loadPrContext } from './pr-common.mjs';

function parsePeriod(period) {
  const p = (period || '30d').trim().toLowerCase();
  const match = p.match(/^(\d+)([dh])$/);
  if (!match) return 30 * 24 * 60 * 60 * 1000;
  const n = parseInt(match[1], 10);
  const unit = match[2];
  if (unit === 'h') return n * 60 * 60 * 1000;
  return n * 24 * 60 * 60 * 1000;
}

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

function htmlEscape(s) {
  return String(s)
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;');
}

function renderHtml(report) {
  const rows = report.items
    .map(
      (p) =>
        `<tr><td>${htmlEscape(p.platform)}</td><td>${htmlEscape(p.repository)}</td><td>${p.id}</td><td>${htmlEscape(
          p.title
        )}</td><td>${htmlEscape(p.state)}</td><td>${htmlEscape(p.updatedAt)}</td></tr>`
    )
    .join('\n');

  return `<!doctype html>
<html>
  <head>
    <meta charset="utf-8" />
    <title>PR Analytics</title>
    <style>
      body { font-family: system-ui, -apple-system, Segoe UI, Roboto, sans-serif; margin: 24px; }
      table { border-collapse: collapse; width: 100%; }
      th, td { border: 1px solid #ddd; padding: 8px; vertical-align: top; }
      th { background: #f6f6f6; text-align: left; }
      .meta { margin-bottom: 16px; }
      .kpi { display: inline-block; margin-right: 18px; }
    </style>
  </head>
  <body>
    <h1>PR Analytics</h1>
    <div class="meta">
      <div class="kpi"><strong>Total:</strong> ${report.metrics.total}</div>
      <div class="kpi"><strong>Open:</strong> ${report.metrics.open}</div>
      <div class="kpi"><strong>Merged:</strong> ${report.metrics.merged}</div>
      <div class="kpi"><strong>Conflicts:</strong> ${report.metrics.conflicts}</div>
      <div class="kpi"><strong>AI Reviewed:</strong> ${report.metrics.aiReviewed}</div>
      <div><strong>Generated:</strong> ${htmlEscape(report.generatedAt)}</div>
      <div><strong>Period:</strong> ${htmlEscape(report.period)}</div>
    </div>
    <table>
      <thead>
        <tr><th>Platform</th><th>Repo</th><th>ID</th><th>Title</th><th>State</th><th>Updated</th></tr>
      </thead>
      <tbody>
        ${rows}
      </tbody>
    </table>
  </body>
</html>`;
}

function main() {
  const args = process.argv.slice(2);
  const period = args[0] || '30d';
  const format = (args[1] || 'html').toLowerCase();
  const outputArg = args[2] || 'pr-report.html';

  const ctx = loadPrContext();
  const prs = loadPRs(ctx.paths.discoveredPrsFile);
  if (prs.length === 0) {
    console.log('❌ No PR data found. Run "pf pr-discover" first.');
    return;
  }

  const cutoff = Date.now() - parsePeriod(period);
  const items = prs.filter((pr) => {
    const updated = new Date(pr.updatedAt || pr.createdAt || 0).getTime();
    return Number.isFinite(updated) ? updated >= cutoff : true;
  });

  const metrics = {
    total: items.length,
    open: items.filter((p) => p.state === 'open').length,
    merged: items.filter((p) => p.state === 'merged').length,
    conflicts: items.filter((p) => p.conflicts).length,
    aiReviewed: items.filter((p) => p.aiReviewed).length,
    byPlatform: items.reduce((acc, p) => {
      acc[p.platform] = (acc[p.platform] || 0) + 1;
      return acc;
    }, {}),
  };

  const report = {
    generatedAt: new Date().toISOString(),
    period,
    metrics,
    items,
  };

  const outPath = path.isAbsolute(outputArg) ? outputArg : path.join(ctx.paths.analyticsDir, outputArg);
  ensureDir(path.dirname(outPath));

  if (format === 'json') {
    fs.writeFileSync(outPath, JSON.stringify(report, null, 2));
  } else {
    fs.writeFileSync(outPath, renderHtml(report));
  }

  console.log(`📈 Analytics written: ${outPath}`);
}

if (import.meta.url === `file://${process.argv[1]}`) {
  main();
}

