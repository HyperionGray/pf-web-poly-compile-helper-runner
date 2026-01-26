#!/usr/bin/env node
/**
 * pf-runner-full execution regression tests
 *
 * Focus: Ensure task parameters (including empty defaults) are available inside
 * `shell |` blocks, so bash scripts using `set -u` don't fail with "unbound variable".
 */

import { spawn } from 'node:child_process';
import { promises as fs } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';
import os from 'node:os';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const projectRoot = join(__dirname, '../..');

class FullRunnerTester {
  constructor() {
    this.passed = 0;
    this.failed = 0;
    this.tests = [];
  }

  runPfFull(args = [], { timeoutMs = 30000 } = {}) {
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

  async withTempPfyfile(contents, fn) {
    const tmpFile = join(os.tmpdir(), `pf-full-runner-${Date.now()}-${Math.random().toString(16).slice(2)}.pf`);
    await fs.writeFile(tmpFile, contents, 'utf-8');
    try {
      return await fn(tmpFile);
    } finally {
      try { await fs.unlink(tmpFile); } catch {}
    }
  }

  assert(condition, message) {
    if (!condition) throw new Error(message);
  }

  assertContains(text, needle, message) {
    if (!text.includes(needle)) throw new Error(message || `Expected output to contain "${needle}"`);
  }

  assertNotContains(text, needle, message) {
    if (text.includes(needle)) throw new Error(message || `Expected output to not contain "${needle}"`);
  }

  async test(name, fn) {
    try {
      console.log(`\n🧪 Testing: ${name}`);
      await fn();
      console.log(`✅ PASS: ${name}`);
      this.passed++;
      this.tests.push({ name, passed: true });
    } catch (err) {
      console.log(`❌ FAIL: ${name}`);
      console.log(`   Error: ${err.message}`);
      this.failed++;
      this.tests.push({ name, passed: false, error: err.message });
    }
  }
}

async function runTests() {
  const t = new FullRunnerTester();

  console.log('🔍 pf-runner-full Execution Unit Tests');
  console.log('======================================\n');

  await t.test('Exports default params into shell | blocks (set -u safe)', async () => {
    const pf = `
task param-env foo=""
  describe Verify params exported to env for shell blocks
  shell_lang bash
  shell |
    set -euo pipefail
    if [ -z "\${foo}" ]; then
      echo "foo-empty"
    else
      echo "foo-set"
    fi
end
`;
    const result = await t.withTempPfyfile(pf, (file) =>
      t.runPfFull(['--file', file, 'run', 'param-env'])
    );
    const combined = `${result.stdout}\n${result.stderr}`;
    t.assert(result.code === 0, `Expected exit code 0, got ${result.code}`);
    t.assertContains(combined, 'foo-empty', 'Expected script to run and print foo-empty');
    t.assertNotContains(combined, 'unbound variable', 'Should not fail due to unset param env');
  });

  await t.test('Real pf-files task distro-install prints usage (no unbound var)', async () => {
    const result = await t.runPfFull(['--file', 'pf-files/Pfyfile.pf', 'run', 'distro-install']);
    const combined = `${result.stdout}\n${result.stderr}`;
    t.assert(result.code === 1, `Expected exit code 1 (usage), got ${result.code}`);
    t.assertContains(combined, 'Usage: pf distro-install', 'Expected usage message from task');
    t.assertNotContains(combined, 'unbound variable', 'Should not fail due to unset distro/packages env');
  });

  await t.test('PATH shim works inside shell | blocks (nested pf call)', async () => {
    const pf = `
task nested-pf
  describe Ensure nested pf invocation resolves via PATH shim
  shell_lang bash
  shell |
    set -euo pipefail
    pf --version >/dev/null
    echo "nested-ok"
end
`;
    const result = await t.withTempPfyfile(pf, (file) =>
      t.runPfFull(['--file', file, 'run', 'nested-pf'])
    );
    const combined = `${result.stdout}\n${result.stderr}`;
    t.assert(result.code === 0, `Expected exit code 0, got ${result.code}`);
    t.assertContains(combined, 'nested-ok', 'Expected nested pf invocation to succeed');
  });

  await t.test('Supports pf-style shell heredoc blocks (shell <<EOF)', async () => {
    const pf = `
task heredoc-marker
  describe Marker-only heredoc should run as a shell script
  shell_lang bash
  shell <<'EOF'
echo "marker-ok"
EOF
end
`;
    const result = await t.withTempPfyfile(pf, (file) =>
      t.runPfFull(['--file', file, 'run', 'heredoc-marker'])
    );
    const combined = `${result.stdout}\n${result.stderr}`;
    t.assert(result.code === 0, `Expected exit code 0, got ${result.code}`);
    t.assertContains(combined, 'marker-ok', 'Expected heredoc script to execute');
  });

  await t.test('Supports bash heredocs in shell lines (shell cat <<EOF)', async () => {
    const pf = `
task heredoc-cat
  describe Command heredoc should be executed as bash
  shell_lang bash
  shell cat << 'EOF'
Hello from heredoc
EOF
end
`;
    const result = await t.withTempPfyfile(pf, (file) =>
      t.runPfFull(['--file', file, 'run', 'heredoc-cat'])
    );
    const combined = `${result.stdout}\n${result.stderr}`;
    t.assert(result.code === 0, `Expected exit code 0, got ${result.code}`);
    t.assertContains(combined, 'Hello from heredoc', 'Expected heredoc content to be printed');
    t.assertNotContains(combined, 'command not found', 'Heredoc content should not be executed as commands');
  });

  await t.test('Preserves indentation inside shell | blocks (python heredoc)', async () => {
    const pf = `
task shell-block-python
  describe shell | blocks should not destroy indentation-sensitive code
  shell_lang bash
  shell |
    python3 - <<'PY'
    x = 1
    if x:
        print("indent-ok")
    PY
end
`;
    const result = await t.withTempPfyfile(pf, (file) =>
      t.runPfFull(['--file', file, 'run', 'shell-block-python'])
    );
    const combined = `${result.stdout}\n${result.stderr}`;
    t.assert(result.code === 0, `Expected exit code 0, got ${result.code}`);
    t.assertContains(combined, 'indent-ok', 'Expected python heredoc to run without indentation errors');
    t.assertNotContains(combined, 'IndentationError', 'Expected no indentation errors');
  });

  await t.test('Real pf-files task pe-help runs (heredoc body not parsed as DSL)', async () => {
    const result = await t.runPfFull(['--file', 'pf-files/Pfyfile.pf', 'run', 'pe-help']);
    const combined = `${result.stdout}\n${result.stderr}`;
    t.assert(result.code === 0, `Expected exit code 0, got ${result.code}`);
    t.assertContains(combined, 'PE Execution and Cross-Platform', 'Expected pe-help output to be printed');
    t.assertNotContains(combined, '[skip] unsupported verb', 'Heredoc body should not be interpreted as DSL');
  });

  console.log('\n=============================');
  console.log('📊 Full Runner Test Results');
  console.log('=============================');
  console.log(`✅ Passed: ${t.passed}`);
  console.log(`❌ Failed: ${t.failed}`);
  console.log(`📈 Success Rate: ${Math.round((t.passed / (t.passed + t.failed)) * 100)}%`);

  if (t.failed === 0) {
    console.log('\n🎉 All full runner tests passed!');
  } else {
    console.log('\n⚠️  Some tests failed. Please review the implementation.');
  }

  return t.failed === 0;
}

if (import.meta.url === `file://${process.argv[1]}`) {
  runTests().then((success) => process.exit(success ? 0 : 1)).catch((err) => {
    console.error('Test runner error:', err);
    process.exit(1);
  });
}

export { runTests, FullRunnerTester };
