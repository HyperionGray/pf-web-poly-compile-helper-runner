#!/usr/bin/env node
/**
 * pf DSL fuzz tester
 *
 * Generates random Pfyfiles and feeds them to pf_parser.py (validate mode).
 * Goals:
 *  - Catch crashes
 *  - Ensure clearly invalid constructs are rejected
 *  - Exercise separators (; && || |), heredocs, shell | blocks, backslash continuations.
 *
 * Keep runs fast: default 200 cases, configurable via PF_FUZZ_CASES.
 */

import { spawn } from 'node:child_process';
import { promises as fs } from 'node:fs';
import { tmpdir } from 'node:os';
import path from 'node:path';

const PROJECT_ROOT = path.resolve(path.join(path.dirname(new URL(import.meta.url).pathname), '../..'));
const PF_RUNNER = path.join(PROJECT_ROOT, 'pf-runner');
const CASES = Number(process.env.PF_FUZZ_CASES || 200);
const SEED = Number(process.env.PF_FUZZ_SEED || 1337);

// Simple PRNG (xorshift32)
function rng(seed) {
  let x = seed >>> 0;
  return () => {
    x ^= x << 13; x >>>= 0;
    x ^= x >>> 17; x >>>= 0;
    x ^= x << 5;  x >>>= 0;
    return x / 0xffffffff;
  };
}

const rand = rng(SEED);
const pick = (arr) => arr[Math.floor(rand() * arr.length)];
const chance = (p) => rand() < p;

const verbs = ['shell', 'env', 'packages', 'service', 'sync'];
const separators = [';', '&&', '||', '|'];
const shellPayloads = [
  'echo "hello"',
  'echo 1 && echo 2',
  'echo a; echo b',
  'true || echo fail',
  'echo left | tr a-z A-Z',
  'printf "%s\\n" line1 line2',
  'cat <<EOF\npayload $VAR\nEOF',
  'cat <<EOF | grep VAR\npayload $VAR\nEOF',
  'echo "\\$notreplaced"',
  'echo "${missing}"',
];

function randomShellLine() {
  let line = pick(shellPayloads);
  if (chance(0.4)) {
    line = line.replace(/\n/g, '\n    ');
    line = 'shell |\n    ' + line.split('\n').join('\n    ');
  } else {
    const sep = pick(separators);
    if (chance(0.5)) line = `${line} ${sep} echo tail`;
    line = `shell ${line}`;
  }
  // backslash continuation occasionally
  if (chance(0.3)) {
    line = line.replace(/ /g, ' \\\n  ');
  }
  return line;
}

function randomPackages() {
  const verbs = ['install', 'remove', 'invalid', '']; // include invalid
  const action = pick(verbs);
  const pkgs = ['clang', 'llvm', 'gcc-multilib', 'weird-pkg', 'foo'];
  const body = [action, pick(pkgs), pick(pkgs)].filter(Boolean).join(' ');
  return `packages ${body}`.trim();
}

function randomService() {
  const actions = ['start', 'stop', 'restart', 'invalid'];
  return `service ${pick(actions)} mysvc`;
}

function randomSync() {
  const bits = [];
  if (chance(0.8)) bits.push('src="/tmp/src"');
  if (chance(0.8)) bits.push('dst="/tmp/dst"');
  if (chance(0.3)) bits.push('recursive');
  if (chance(0.3)) bits.push('delete');
  return `sync ${bits.join(' ')}`.trim();
}

function randomEnv() {
  return `env KEY${Math.floor(rand() * 10)}=value${Math.floor(rand() * 10)}`;
}

function randomTask(i) {
  const body = [];
  const lines = 3 + Math.floor(rand() * 4);
  for (let j = 0; j < lines; j++) {
    const verb = pick(verbs);
    if (verb === 'shell') body.push(randomShellLine());
    else if (verb === 'packages') body.push(randomPackages());
    else if (verb === 'service') body.push(randomService());
    else if (verb === 'sync') body.push(randomSync());
    else if (verb === 'env') body.push(randomEnv());
  }
  // Maybe break structure: missing end or nested task
  const maybeDropEnd = chance(0.05);
  const maybeNestedTask = chance(0.05);
  const header = `task fuzz-${i} param="${i}"`;
  const footer = maybeDropEnd ? '' : 'end';
  if (maybeNestedTask) body.splice(1, 0, 'task nested\n  shell echo nested\nend');
  return [header, ...body, footer].filter(Boolean).join('\n');
}

async function runCase(idx, pfContent) {
  const tmpFile = path.join(tmpdir(), `pf-fuzz-${process.pid}-${idx}.pf`);
  await fs.writeFile(tmpFile, pfContent, 'utf-8');
  return new Promise((resolve) => {
    const proc = spawn('python3', ['pf_parser.py', 'validate', `--file=${tmpFile}`], {
      cwd: PF_RUNNER,
      stdio: ['ignore', 'pipe', 'pipe'],
      timeout: 8000,
    });
    let stdout = '';
    let stderr = '';
    proc.stdout.on('data', (d) => { stdout += d.toString(); });
    proc.stderr.on('data', (d) => { stderr += d.toString(); });
    proc.on('close', async (code) => {
      try { await fs.unlink(tmpFile); } catch { /* ignore */ }
      resolve({ code, stdout, stderr });
    });
    proc.on('error', (err) => resolve({ code: -1, stdout, stderr: err.message }));
  });
}

async function main() {
  let failures = 0;
  for (let i = 0; i < CASES; i++) {
    const pf = randomTask(i);
    const { code, stderr } = await runCase(i, pf);

    // Should not crash; code -1 indicates spawn error/timeout
    if (code === -1) {
      console.error(`[FATAL] spawn/timeout on case ${i}\n${pf}\n${stderr}`);
      failures++;
      break;
    }

    // If invalid constructs are accepted, flag when we intentionally injected "invalid" verb
    const hasTopLevelInvalidPackages = pf.split('\n').some(
      (l) => l.startsWith('packages invalid')
    );
    if (hasTopLevelInvalidPackages && code === 0) {
      console.error(`[BUG] invalid packages accepted (case ${i})\n${pf}`);
      failures++;
      break;
    }
  }

  if (failures > 0) {
    console.error(`Fuzzing found ${failures} issue(s).`);
    process.exit(1);
  }

  console.log(`Fuzzing complete. Cases: ${CASES}, Seed: ${SEED}`);
}

main().catch((err) => {
  console.error('Fuzzer crashed:', err);
  process.exit(1);
});
