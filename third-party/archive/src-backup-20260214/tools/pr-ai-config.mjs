#!/usr/bin/env node

/**
 * PR AI Config
 * Writes provider credentials/settings to the configured aiProvidersFile.
 * (No env-var configuration.)
 */

import fs from 'node:fs';

import { loadPrContext, writeJson } from './pr-common.mjs';

function tryParseJson(value) {
  if (!value || typeof value !== 'string') return null;
  try {
    return JSON.parse(value);
  } catch {
    return null;
  }
}

function main() {
  const args = process.argv.slice(2);
  const provider = args[0];
  const apiKey = args[1];
  const model = args[2];
  const reviewCriteriaRaw = args[3];

  if (!provider) {
    console.error('❌ Missing provider');
    console.log('Usage: node tools/pr-ai-config.mjs <provider> <api_key> [model] [review_criteria_json]');
    process.exitCode = 1;
    return;
  }

  const ctx = loadPrContext();
  const outPath = ctx.paths.aiProvidersFile;

  const current = ctx.pr.ai && typeof ctx.pr.ai === 'object' ? ctx.pr.ai : {};
  const updated = structuredClone(current);

  updated.providers ||= {};
  updated.providers[provider] ||= {};

  if (apiKey !== undefined) updated.providers[provider].apiKey = apiKey || null;
  if (model !== undefined && model !== null && model !== '') updated.providers[provider].model = model;
  updated.providers[provider].enabled = !!updated.providers[provider].apiKey;

  const criteria = tryParseJson(reviewCriteriaRaw);
  if (criteria && typeof criteria === 'object' && !Array.isArray(criteria)) {
    updated.reviewCriteria ||= {};
    updated.reviewCriteria = { ...updated.reviewCriteria, ...criteria };
  }

  writeJson(outPath, updated);
  console.log(`✅ AI provider config updated: ${outPath}`);
  console.log(`- provider: ${provider}`);
  console.log(`- enabled: ${updated.providers[provider].enabled}`);
}

if (import.meta.url === `file://${process.argv[1]}`) {
  main();
}

