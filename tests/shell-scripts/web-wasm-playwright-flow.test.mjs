#!/usr/bin/env node

import { spawn } from 'node:child_process';
import { promises as fs } from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const projectRoot = path.resolve(path.join(__dirname, '../..'));
const runnerPath = path.join(projectRoot, 'pf-runner', 'pf_main.py');
const webPfyPath = path.join(projectRoot, 'pf-files', 'web-testing', 'Pfyfile.web.pf');
const TASK_TIMEOUT = 120000;
const RECORD_SEPARATOR = '\t';

class FlowTester {
  constructor() {
    this.passed = 0;
    this.failed = 0;
  }

  async test(name, fn) {
    try {
      await fn();
      console.log(`[PASS] ${name}`);
      this.passed += 1;
    } catch (error) {
      console.log(`[FAIL] ${name}`);
      console.log(`  ${error.message}`);
      this.failed += 1;
    }
  }

  summary() {
    console.log('\n=============================');
    console.log('Web WASM + Playwright Flow');
    console.log('=============================');
    console.log(`Passed: ${this.passed}`);
    console.log(`Failed: ${this.failed}`);
    return this.failed === 0;
  }
}

async function writeExecutable(filePath, content) {
  await fs.writeFile(filePath, content, { mode: 0o755 });
}

function runTask(taskName, options) {
  return new Promise((resolve, reject) => {
    const proc = spawn('python3', [runnerPath, taskName, `--file=${webPfyPath}`], {
      cwd: options.cwd,
      env: options.env,
      stdio: ['ignore', 'pipe', 'pipe'],
      timeout: TASK_TIMEOUT,
    });

    let stdout = '';
    let stderr = '';
    proc.stdout.on('data', (chunk) => {
      stdout += chunk.toString();
    });
    proc.stderr.on('data', (chunk) => {
      stderr += chunk.toString();
    });

    proc.on('close', (code) => resolve({ code, stdout, stderr }));
    proc.on('error', reject);
  });
}

async function readRecordLines(recordFile) {
  const raw = await fs.readFile(recordFile, 'utf-8');
  return raw
    .trim()
    .split('\n')
    .filter(Boolean)
    .map((line) => {
      const [tool, runId, headless, slowMo, args] = line.split(RECORD_SEPARATOR);
      return { tool, runId, headless, slowMo, args };
    });
}

async function setupHarness(tempRoot, recordFile) {
  const binDir = path.join(tempRoot, 'bin');
  await fs.mkdir(binDir, { recursive: true });
  await fs.mkdir(path.join(tempRoot, 'pf-files', 'web-testing'), { recursive: true });

  const sourceConfig = path.join(projectRoot, 'pf-files', 'web-testing', 'playwright.config.ts');
  const targetConfig = path.join(tempRoot, 'pf-files', 'web-testing', 'playwright.config.ts');
  await fs.copyFile(sourceConfig, targetConfig);

  await fs.mkdir(path.join(tempRoot, 'demos', 'pf-web-polyglot-demo-plus-c', 'rust'), { recursive: true });
  await fs.mkdir(path.join(tempRoot, 'demos', 'pf-web-polyglot-demo-plus-c', 'c'), { recursive: true });
  await fs.mkdir(path.join(tempRoot, 'demos', 'pf-web-polyglot-demo-plus-c', 'fortran', 'src'), { recursive: true });
  await fs.mkdir(path.join(tempRoot, 'demos', 'pf-web-polyglot-demo-plus-c', 'asm'), { recursive: true });

  await fs.writeFile(path.join(tempRoot, 'demos', 'pf-web-polyglot-demo-plus-c', 'c', 'c_trap.c'), 'int main(){return 0;}');
  await fs.writeFile(path.join(tempRoot, 'demos', 'pf-web-polyglot-demo-plus-c', 'fortran', 'src', 'hello.f90'), 'program hello\nend');
  await fs.writeFile(path.join(tempRoot, 'demos', 'pf-web-polyglot-demo-plus-c', 'asm', 'mini.wat'), '(module)');

  // Shared shell snippet used by tool stubs to record environment propagation.
  const recordSnippet = [
    // ${0##*/} extracts the current script basename so we capture the invoked tool.
    `tool="${'$'}{0##*/}"`,
    `run_id="${'$'}{PF_WEB_RUN_ID:-}"`,
    `headless="${'$'}{PF_PLAYWRIGHT_HEADLESS:-}"`,
    `slowmo="${'$'}{PF_PLAYWRIGHT_SLOWMO:-}"`,
    `printf '%s${RECORD_SEPARATOR}%s${RECORD_SEPARATOR}%s${RECORD_SEPARATOR}%s${RECORD_SEPARATOR}%s\\n' "${'$'}tool" "${'$'}run_id" "${'$'}headless" "${'$'}slowmo" "${'$'}*" >> "${recordFile}"`,
  ].join('\n');

  await writeExecutable(
    path.join(binDir, 'pf'),
    `#!/usr/bin/env bash
set -euo pipefail
python3 "${runnerPath}" "$@"
`,
  );

  await writeExecutable(
    path.join(binDir, 'git'),
    `#!/usr/bin/env bash
set -euo pipefail
if [ "${'$'}{1:-}" = "rev-parse" ] && [ "${'$'}{2:-}" = "--show-toplevel" ]; then
  echo "${tempRoot}"
  exit 0
fi
exit 0
`,
  );

  await writeExecutable(
    path.join(binDir, 'wasm-pack'),
    `#!/usr/bin/env bash
set -euo pipefail
${recordSnippet}
outdir=""
outname="rust_demo"
while [ "$#" -gt 0 ]; do
  case "$1" in
    --out-dir) outdir="$2"; shift 2 ;;
    --out-name) outname="$2"; shift 2 ;;
    *) shift ;;
  esac
done
mkdir -p "$outdir"
printf 'export function greet(){}\\n' > "$outdir/$outname.js"
printf '\\0' > "$outdir/${'$'}{outname}_bg.wasm"
`,
  );

  await writeExecutable(
    path.join(binDir, 'emcc'),
    `#!/usr/bin/env bash
set -euo pipefail
${recordSnippet}
out=""
while [ "$#" -gt 0 ]; do
  if [ "$1" = "-o" ]; then
    out="$2"
    break
  fi
  shift
done
mkdir -p "$(dirname "$out")"
printf 'export default {}\\n' > "$out"
printf '\\0' > "${'$'}{out%.js}.wasm"
`,
  );

  await writeExecutable(
    path.join(binDir, 'lfortran'),
    `#!/usr/bin/env bash
set -euo pipefail
${recordSnippet}
out=""
while [ "$#" -gt 0 ]; do
  if [ "$1" = "-o" ]; then
    out="$2"
    break
  fi
  shift
done
mkdir -p "$(dirname "$out")"
printf 'native-fortran\\n' > "$out"
`,
  );

  await writeExecutable(
    path.join(binDir, 'wat2wasm'),
    `#!/usr/bin/env bash
set -euo pipefail
${recordSnippet}
out=""
while [ "$#" -gt 0 ]; do
  if [ "$1" = "-o" ]; then
    out="$2"
    break
  fi
  shift
done
mkdir -p "$(dirname "$out")"
printf '\\0asm' > "$out"
`,
  );

  await writeExecutable(
    path.join(binDir, 'npx'),
    `#!/usr/bin/env bash
set -euo pipefail
${recordSnippet}
args=" $* "
echo "$args" | grep -q " playwright test " || { echo "npx stub validation failed: missing 'playwright test'" >&2; exit 1; }
`,
  );

  return binDir;
}

async function runTests() {
  const tester = new FlowTester();
  const tempRoot = await fs.mkdtemp(path.join(os.tmpdir(), 'pf-web-flow-'));
  const recordFile = path.join(tempRoot, 'tool-record.log');

  try {
    const binDir = await setupHarness(tempRoot, recordFile);
    const env = {
      ...process.env,
      PATH: `${binDir}:${process.env.PATH || ''}`,
      PFY_ROOT: tempRoot,
      PF_TEST_RECORD: recordFile,
    };

    await tester.test('build-and-test-visible executes wasm build + playwright abstraction', async () => {
      const result = await runTask('build-and-test-visible', { cwd: tempRoot, env });
      if (result.code !== 0) {
        throw new Error(`Task failed (code=${result.code}): ${result.stderr || result.stdout}`);
      }
    });

    await tester.test('all wasm outputs are generated from real pf tasks', async () => {
      const expected = [
        path.join(tempRoot, 'demos', 'pf-web-polyglot-demo-plus-c', 'web', 'wasm', 'rust', 'pkg', 'rust_demo.js'),
        path.join(tempRoot, 'demos', 'pf-web-polyglot-demo-plus-c', 'web', 'wasm', 'c', 'c_trap.js'),
        path.join(tempRoot, 'demos', 'pf-web-polyglot-demo-plus-c', 'web', 'wasm', 'fortran', 'fortran.native'),
        path.join(tempRoot, 'demos', 'pf-web-polyglot-demo-plus-c', 'web', 'wasm', 'asm', 'mini.wasm'),
      ];
      for (const artifact of expected) {
        await fs.access(artifact);
      }
    });

    await tester.test('single predictable environment is propagated to all tool calls', async () => {
      const records = await readRecordLines(recordFile);
      const expectedTools = new Set(['wasm-pack', 'emcc', 'lfortran', 'wat2wasm', 'npx']);
      for (const tool of expectedTools) {
        if (!records.find((r) => r.tool === tool)) {
          throw new Error(`Missing tool invocation record for ${tool}`);
        }
      }
      const runIds = new Set(records.map((r) => r.runId).filter(Boolean));
      if (runIds.size !== 1) {
        throw new Error(`Expected exactly one PF_WEB_RUN_ID, got ${runIds.size}`);
      }
      const npxRecord = records.find((r) => r.tool === 'npx');
      if (!npxRecord || npxRecord.headless !== 'false') {
        throw new Error('Playwright abstraction did not force headed mode');
      }
      if (!npxRecord.slowMo || Number(npxRecord.slowMo) < 0) {
        throw new Error('Playwright abstraction did not set slow-mo');
      }
    });
  } finally {
    await fs.rm(tempRoot, { recursive: true, force: true });
  }

  return tester.summary();
}

if (import.meta.url === `file://${process.argv[1]}`) {
  runTests()
    .then((ok) => process.exit(ok ? 0 : 1))
    .catch((error) => {
      console.error(error);
      process.exit(1);
    });
}

export { runTests };
