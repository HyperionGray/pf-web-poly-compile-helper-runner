#!/usr/bin/env node

/**
 * PR Webhook Setup (safe / non-destructive)
 * Writes a local webhook config stub and prints setup instructions.
 */

import path from 'node:path';

import { ensureDir, loadPrContext, writeJson } from './pr-common.mjs';

function main() {
  const args = process.argv.slice(2);
  const endpointUrl = args[0];
  const secret = args[1];

  if (!endpointUrl || !secret) {
    console.error('❌ Missing required arguments');
    console.log('Usage: node tools/pr-webhook-setup.mjs <endpoint_url> <secret>');
    process.exitCode = 1;
    return;
  }

  const ctx = loadPrContext();
  const filePath = path.join(ctx.paths.storageDir, 'pr-webhooks.json');
  ensureDir(ctx.paths.storageDir);

  const config = {
    timestamp: new Date().toISOString(),
    endpointUrl,
    secret,
    notes: [
      'Store secrets in a user-scoped config (e.g. ~/.config/pf/pf.config.json5) when possible.',
      'This file is written for convenience; rotate secrets if committed accidentally.',
    ],
  };

  writeJson(filePath, config);
  console.log(`💾 Webhook config written: ${filePath}`);
  console.log('');
  console.log('GitHub: Settings → Webhooks → Add webhook');
  console.log(`- Payload URL: ${endpointUrl}`);
  console.log('- Content type: application/json');
  console.log('- Secret: (use the provided secret)');
  console.log('- Events: pull_request, pull_request_review, push (as needed)');
  console.log('');
  console.log('GitLab: Settings → Webhooks');
  console.log(`- URL: ${endpointUrl}`);
  console.log('- Secret token: (use the provided secret)');
  console.log('- Triggers: Merge request events, Push events (as needed)');
}

if (import.meta.url === `file://${process.argv[1]}`) {
  main();
}

