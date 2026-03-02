import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';

import { getConfigValue, loadPfConfig, resolveHomePath } from './pf-config.mjs';

function isPlainObject(value) {
  return value && typeof value === 'object' && !Array.isArray(value);
}

function fillMissing(base, fallback) {
  if (base === undefined || base === null) return fallback;

  if (Array.isArray(base)) {
    if (base.length === 0 && Array.isArray(fallback) && fallback.length > 0) return fallback;
    return base;
  }

  if (isPlainObject(base) && isPlainObject(fallback)) {
    const out = { ...base };
    for (const [key, val] of Object.entries(fallback)) {
      out[key] = key in out ? fillMissing(out[key], val) : val;
    }
    return out;
  }

  if (base === '' && fallback !== undefined && fallback !== null && fallback !== '') return fallback;
  return base;
}

function resolvePrPath(storageDir, value, fallback) {
  const resolved = resolveHomePath(value ?? fallback);
  if (!resolved) return resolved;
  if (path.isAbsolute(resolved)) return resolved;
  return path.join(storageDir, resolved);
}

export function ensureDir(dirPath) {
  fs.mkdirSync(dirPath, { recursive: true });
}

export function readJsonIfExists(filePath) {
  try {
    if (!filePath) return null;
    if (!fs.existsSync(filePath)) return null;
    const raw = fs.readFileSync(filePath, 'utf-8');
    return JSON.parse(raw);
  } catch {
    return null;
  }
}

export function writeJson(filePath, data) {
  ensureDir(path.dirname(filePath));
  fs.writeFileSync(filePath, JSON.stringify(data, null, 2));
}

export function parseBool(value, defaultValue = false) {
  if (typeof value === 'boolean') return value;
  if (typeof value === 'number') return value !== 0;
  if (typeof value !== 'string') return defaultValue;
  const v = value.trim().toLowerCase();
  if (['1', 'true', 'yes', 'y', 'on'].includes(v)) return true;
  if (['0', 'false', 'no', 'n', 'off'].includes(v)) return false;
  return defaultValue;
}

export function loadPrContext(startDir = process.cwd()) {
  const { config, path: pfConfigPath } = loadPfConfig(startDir);

  const storageDir = resolveHomePath(getConfigValue(config, 'pr.storageDir', '~/.config/pf'));
  const paths = {
    storageDir,
    discoveryConfigFile: resolvePrPath(
      storageDir,
      getConfigValue(config, 'pr.discoveryConfigFile', null),
      path.join(storageDir, 'pr-config.json')
    ),
    discoveredPrsFile: resolvePrPath(
      storageDir,
      getConfigValue(config, 'pr.discoveredPrsFile', null),
      path.join(storageDir, 'discovered-prs.json')
    ),
    aiProvidersFile: resolvePrPath(
      storageDir,
      getConfigValue(config, 'pr.aiProvidersFile', null),
      path.join(storageDir, 'ai-providers.json')
    ),
    reviewsDir: resolvePrPath(storageDir, getConfigValue(config, 'pr.reviewsDir', null), path.join(storageDir, 'reviews')),
    batchReviewsDir: resolvePrPath(
      storageDir,
      getConfigValue(config, 'pr.batchReviewsDir', null),
      path.join(storageDir, 'batch-reviews')
    ),
    conflictAnalysisDir: resolvePrPath(
      storageDir,
      getConfigValue(config, 'pr.conflictAnalysisDir', null),
      path.join(storageDir, 'conflict-analysis')
    ),
    mergeBackupsDir: resolvePrPath(
      storageDir,
      getConfigValue(config, 'pr.mergeBackupsDir', null),
      path.join(storageDir, 'merge-backups')
    ),
    mergeResultsDir: resolvePrPath(
      storageDir,
      getConfigValue(config, 'pr.mergeResultsDir', null),
      path.join(storageDir, 'merge-results')
    ),
    analyticsDir: resolvePrPath(
      storageDir,
      getConfigValue(config, 'pr.analyticsDir', null),
      path.join(storageDir, 'analytics')
    ),
  };

  const legacyPrConfig = readJsonIfExists(paths.discoveryConfigFile) || {};
  const legacyAiProviders = readJsonIfExists(paths.aiProvidersFile) || {};

  const repositories = (() => {
    const cfgRepos = getConfigValue(config, 'pr.repositories', []);
    if (Array.isArray(cfgRepos) && cfgRepos.length > 0) return cfgRepos;
    const legacyRepos = legacyPrConfig.repositories;
    if (Array.isArray(legacyRepos) && legacyRepos.length > 0) return legacyRepos;
    return [];
  })();

  const platforms = fillMissing(getConfigValue(config, 'pr.platforms', {}), legacyPrConfig.platforms || {});
  const filters = fillMissing(getConfigValue(config, 'pr.filters', {}), legacyPrConfig.filters || {});
  const ai = fillMissing(getConfigValue(config, 'pr.ai', {}), legacyAiProviders || {});

  // Normalize provider enablement based on key presence (no env-var config).
  if (isPlainObject(ai.providers)) {
    for (const provider of Object.values(ai.providers)) {
      if (!isPlainObject(provider)) continue;
      const apiKey = provider.apiKey;
      if (typeof provider.enabled !== 'boolean') provider.enabled = !!apiKey;
      if (!provider.enabled && apiKey) provider.enabled = true;
    }
  }

  return {
    pf: { config, path: pfConfigPath },
    paths,
    pr: {
      repositories,
      platforms,
      filters,
      ai,
    },
    runtime: {
      homeDir: os.homedir(),
    },
  };
}

