#!/usr/bin/env node
import { spawn } from 'node:child_process';
import { promises as fs } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';
import os from 'node:os';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const projectRoot = join(__dirname, '../..');

function run(command) {
  return new Promise((resolve) => {
    const proc = spawn('bash', ['-lc', command], {
      cwd: projectRoot,
      stdio: ['ignore', 'pipe', 'pipe'],
      timeout: 120000
    });
    let stdout = '';
    let stderr = '';
    proc.stdout.on('data', (d) => { stdout += d.toString(); });
    proc.stderr.on('data', (d) => { stderr += d.toString(); });
    proc.on('close', (code) => resolve({ code, stdout, stderr }));
    proc.on('error', (err) => resolve({ code: -1, stdout, stderr: err.message }));
  });
}

function assert(condition, message) {
  if (!condition) throw new Error(message);
}

async function main() {
  const tmpDir = join(os.tmpdir(), `pf-fuzzing-task-test-${Date.now()}`);
  const templatePath = join(tmpDir, 'nested', 'fuzz_target.c');
  const fuzzerPath = join(tmpDir, 'fuzzer');

  await fs.mkdir(tmpDir, { recursive: true });

  const envPrefix = 'PF_PYTHON=/usr/bin/python3';
  const genCmd = `${envPrefix} ./pf.sh --file pf/Pfyfile.fuzzing.pf generate-libfuzzer-template output=${templatePath}`;
  const buildCmd = `${envPrefix} ./pf.sh --file pf/Pfyfile.fuzzing.pf build-libfuzzer-target source=fuzzing/fuzz_target.c output=${fuzzerPath}`;

  const gen = await run(genCmd);
  assert(gen.code === 0, `generate-libfuzzer-template failed:\n${gen.stdout}\n${gen.stderr}`);
  await fs.access(templatePath);

  const build = await run(buildCmd);
  assert(build.code === 0, `build-libfuzzer-target failed:\n${build.stdout}\n${build.stderr}`);
  await fs.access(fuzzerPath);

  console.log('Fuzzing pf task regression checks passed.');
}

main().catch((err) => {
  console.error(err.message);
  process.exit(1);
});
