import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';

let JSON5;
try {
  // json5 is commonly available via npm or system packages (e.g. /usr/share/nodejs/json5).
  // We keep this as a runtime dependency so repo scripts work without env-var config.
  JSON5 = (await import('json5')).default;
} catch (err) {
  throw new Error(
    "Missing dependency 'json5'. Install it with: npm install json5\n" +
      `Original error: ${err?.message || err}`
  );
}

const DEFAULT_CONFIG = {
  pfy: { file: 'Pfyfile.pf', searchParents: 'git' },
  runner: {
    autocorrect: { mode: 'auto', threshold: 0.75 },
    pathAutofix: true,
    playwright: { headful: false },
  },
  api: { host: '127.0.0.1', port: 8000, workers: 4 },
  container: { runtime: 'podman', image: 'localhost/pf-runner:latest' },
  pr: {
    storageDir: '~/.config/pf',
    discoveryConfigFile: '~/.config/pf/pr-config.json',
    discoveredPrsFile: '~/.config/pf/discovered-prs.json',
    aiProvidersFile: '~/.config/pf/ai-providers.json',
    repositories: [],
    platforms: { github: { enabled: true }, gitlab: { enabled: true } },
    filters: { states: ['open'], labels: [], authors: [] },
    ai: {
      providers: {
        openai: { apiKey: null, model: 'gpt-4', enabled: false },
        anthropic: { apiKey: null, model: 'claude-3-sonnet-20240229', enabled: false },
      },
      reviewCriteria: {
        security: true,
        performance: true,
        maintainability: true,
        testCoverage: true,
        documentation: true,
      },
    },
  },
  github: { repoOwner: 'P4X-ng', repoName: 'pf-web-poly-compile-helper-runner', token: null },
  devEnvironment: { useQuadlet: true, gpuSupport: false },
  os: { distroArtifactsDir: '~/.pf/distros', switchBaseDir: '~/.pf/os-switch' },
};

function deepMerge(base, override) {
  const out = { ...base };
  for (const [key, value] of Object.entries(override || {})) {
    if (
      value &&
      typeof value === 'object' &&
      !Array.isArray(value) &&
      out[key] &&
      typeof out[key] === 'object' &&
      !Array.isArray(out[key])
    ) {
      out[key] = deepMerge(out[key], value);
    } else {
      out[key] = value;
    }
  }
  return out;
}

function gitRoot(startDir) {
  let cur = path.resolve(startDir);
  while (true) {
    if (fs.existsSync(path.join(cur, '.git'))) return cur;
    const parent = path.dirname(cur);
    if (parent === cur) return null;
    cur = parent;
  }
}

export function findPfConfigPath(startDir = process.cwd()) {
  const start = path.resolve(startDir);
  const stop = gitRoot(start) || path.parse(start).root;

  let cur = start;
  while (true) {
    const candidate = path.join(cur, 'pf.config.json5');
    if (fs.existsSync(candidate) && fs.statSync(candidate).isFile()) return candidate;

    if (cur === stop) break;
    const parent = path.dirname(cur);
    if (parent === cur) break;
    cur = parent;
  }

  const home = os.homedir();
  const userCandidates = [
    path.join(home, '.config', 'pf', 'pf.config.json5'),
    path.join(home, '.pf', 'pf.config.json5'),
  ];
  for (const candidate of userCandidates) {
    if (fs.existsSync(candidate) && fs.statSync(candidate).isFile()) return candidate;
  }

  return null;
}

export function loadPfConfig(startDir = process.cwd()) {
  const configPath = findPfConfigPath(startDir);
  if (!configPath) return { config: { ...DEFAULT_CONFIG }, path: null };

  const raw = fs.readFileSync(configPath, 'utf-8');
  const parsed = JSON5.parse(raw);
  if (!parsed || typeof parsed !== 'object' || Array.isArray(parsed)) {
    throw new Error(`Invalid config root (expected object): ${configPath}`);
  }

  return { config: deepMerge(DEFAULT_CONFIG, parsed), path: configPath };
}

export function getConfigValue(config, dottedKey, defaultValue) {
  let cur = config;
  for (const part of dottedKey.split('.')) {
    if (!cur || typeof cur !== 'object' || Array.isArray(cur) || !(part in cur)) return defaultValue;
    cur = cur[part];
  }
  return cur ?? defaultValue;
}

export function resolveHomePath(value) {
  if (typeof value !== 'string') return value;
  if (value.startsWith('~/')) return path.join(os.homedir(), value.slice(2));
  if (value === '~') return os.homedir();
  return value;
}
