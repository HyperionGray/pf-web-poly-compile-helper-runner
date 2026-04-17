#!/usr/bin/env node

import { spawn } from 'node:child_process';
import { promises as fs } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const projectRoot = join(__dirname, '../..');

function runPfFull(args = [], timeoutMs = 30000) {
  return new Promise((resolve) => {
    const proc = spawn('python3', ['pf-runner-full/pf_main.py', ...args], {
      cwd: projectRoot,
      stdio: ['ignore', 'pipe', 'pipe'],
      timeout: timeoutMs
    });

    let stdout = '';
    let stderr = '';
    proc.stdout.on('data', (d) => { stdout += d.toString(); });
    proc.stderr.on('data', (d) => { stderr += d.toString(); });
    proc.on('close', (code) => resolve({ code, stdout, stderr }));
    proc.on('error', (err) => resolve({ code: -1, stdout, stderr: err.message }));
  });
}

async function listPfFiles(dir) {
  const entries = await fs.readdir(dir, { withFileTypes: true });
  const files = [];
  for (const entry of entries) {
    const abs = join(dir, entry.name);
    if (entry.isDirectory()) {
      files.push(...await listPfFiles(abs));
      continue;
    }
    if (entry.isFile() && entry.name.endsWith('.pf')) {
      files.push(abs.slice(projectRoot.length + 1));
    }
  }
  return files.sort();
}

async function main() {
  let passed = 0;
  let failed = 0;

  const assert = (cond, msg) => {
    if (!cond) throw new Error(msg);
  };

  const test = async (name, fn) => {
    try {
      process.stdout.write(`TEST ${name}... `);
      await fn();
      console.log('PASS');
      passed++;
    } catch (err) {
      console.log('FAIL');
      console.log(`   ${err.message}`);
      failed++;
    }
  };

  console.log('pf directory review tests');
  console.log('=========================');

  await test('pf/Pfyfile.pf validates', async () => {
    const result = await runPfFull(['--file', 'pf/Pfyfile.pf', 'validate']);
    assert(result.code === 0, `validate failed (${result.code}): ${result.stderr || result.stdout}`);
  });

  await test('hgactions module is reachable from pf/Pfyfile.pf list', async () => {
    const result = await runPfFull(['--file', 'pf/Pfyfile.pf', 'list']);
    assert(result.code === 0, `list failed (${result.code}): ${result.stderr || result.stdout}`);
    assert(result.stdout.includes('hgactions (1 task)'), 'expected hgactions module in list output');
  });

  await test('all pf/**/*.pf files parse with current runner', async () => {
    const files = await listPfFiles(join(projectRoot, 'pf'));
    const failures = [];

    for (const file of files) {
      const result = await runPfFull(['--file', file, 'validate']);
      if (result.code !== 0) {
        failures.push({ file, code: result.code, stderr: result.stderr.trim(), stdout: result.stdout.trim() });
      }
    }

    if (failures.length > 0) {
      const preview = failures
        .slice(0, 5)
        .map((f) => `${f.file} (code ${f.code}) ${f.stderr || f.stdout}`)
        .join('\n');
      throw new Error(`found ${failures.length} pf file validation failures\n${preview}`);
    }
  });

  console.log('\nResults');
  console.log('-------');
  console.log(`Passed: ${passed}`);
  console.log(`Failed: ${failed}`);
  process.exit(failed === 0 ? 0 : 1);
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
