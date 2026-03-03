#!/usr/bin/env node
/**
 * Unit Tests for pf prune functionality
 * 
 * Tests the syntax checking, dry-run, and debug mode features
 */

import { spawn } from 'child_process';
import { promises as fs } from 'fs';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';
import os from 'os';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const projectRoot = join(__dirname, '../..');
const pfRunnerDir = join(projectRoot, 'pf-runner');

// Test utilities
class PruneTester {
    constructor() {
        this.passed = 0;
        this.failed = 0;
        this.tests = [];
    }

    async runPfCommand(args, pfContent = null) {
        let tmpFile = null;
        
        if (pfContent !== null) {
            tmpFile = join(os.tmpdir(), `pf-prune-test-${Date.now()}.pf`);
            await fs.writeFile(tmpFile, pfContent, 'utf-8');
        }
        
        return new Promise((resolve, reject) => {
            const cmdArgs = ['pf_parser.py'];
            if (tmpFile) {
                cmdArgs.push(tmpFile);
            }
            cmdArgs.push(...args);
            
            const proc = spawn('python3', cmdArgs, {
                cwd: pfRunnerDir,
                stdio: ['pipe', 'pipe', 'pipe'],
                timeout: 30000
            });

            let stdout = '';
            let stderr = '';

            proc.stdout.on('data', (data) => {
                stdout += data.toString();
            });

            proc.stderr.on('data', (data) => {
                stderr += data.toString();
            });

            proc.on('close', async (code) => {
                if (tmpFile) {
                    try { await fs.unlink(tmpFile); } catch {}
                }
                resolve({ code, stdout: stdout.trim(), stderr: stderr.trim() });
            });

            proc.on('error', (error) => {
                reject(error);
            });
        });
    }

    async test(name, testFn) {
        let testPassed = false;
        try {
            console.log(`\n🧪 Testing: ${name}`);
            await testFn();
            console.log(`✅ PASS: ${name}`);
            this.passed++;
            testPassed = true;
        } catch (error) {
            console.log(`❌ FAIL: ${name}`);
            console.log(`   Error: ${error.message}`);
            this.failed++;
        }
        this.tests.push({ name, passed: testPassed });
    }

    assertEqual(actual, expected, message = '') {
        if (actual !== expected) {
            throw new Error(`${message}: Expected ${expected}, got ${actual}`);
        }
    }

    assertIncludes(text, pattern, message = '') {
        if (!text.includes(pattern)) {
            throw new Error(`${message}: Expected text to include "${pattern}"`);
        }
    }
}

// Test cases
async function runTests() {
    const tester = new PruneTester();
    
    console.log('🔍 pf prune Unit Tests');
    console.log('======================\n');

    // ==========================================
    // SECTION 1: Basic Prune Command
    // ==========================================
    console.log('\n--- Section 1: Basic Prune Command ---');

    await tester.test('Prune command exists', async () => {
        const result = await tester.runPfCommand(['--help']);
        tester.assertIncludes(result.stdout, 'prune', 'Help should mention prune command');
    });

    await tester.test('Prune command runs', async () => {
        const validPf = `
task valid
  describe Valid task
  shell echo "hello"
end
`;
        const result = await tester.runPfCommand(['prune'], validPf);
        tester.assertEqual(result.code, 0, 'Valid file should pass prune');
    });

    await tester.test('Prune detects missing end', async () => {
        const brokenPf = `
task broken
  describe Broken task
  shell echo "hello"
`;
        const result = await tester.runPfCommand(['prune'], brokenPf);
        tester.assertEqual(result.code, 1, 'File with missing end should fail');
        tester.assertIncludes(result.stdout, 'missing', 'Error should mention missing end');
    });

    await tester.test('Prune detects invalid operator ===', async () => {
        const brokenPf = `
task broken
  describe Broken task
  if $var === "value"
    shell echo "hello"
  end
end
`;
        const result = await tester.runPfCommand(['prune'], brokenPf);
        tester.assertEqual(result.code, 1, 'File with === should fail');
        tester.assertIncludes(result.stdout, '===', 'Error should mention === operator');
    });

    await tester.test('Prune detects missing in keyword', async () => {
        const brokenPf = `
task broken
  describe Broken task
  for item ["a", "b"]
    shell echo $item
  end
end
`;
        const result = await tester.runPfCommand(['prune'], brokenPf);
        tester.assertEqual(result.code, 1, 'File with missing in should fail');
        tester.assertIncludes(result.stdout, 'in', 'Error should mention missing in');
    });

    await tester.test('Prune detects invalid packages action', async () => {
        const brokenPf = `
task broken
  describe Broken task
  packages invalidaction package-name
end
`;
        const result = await tester.runPfCommand(['prune'], brokenPf);
        tester.assertEqual(result.code, 1, 'File with invalid packages action should fail');
        tester.assertIncludes(result.stdout, 'install', 'Error should suggest valid actions');
    });

    await tester.test('Prune detects invalid service action', async () => {
        const brokenPf = `
task broken
  describe Broken task
  service invalidaction nginx
end
`;
        const result = await tester.runPfCommand(['prune'], brokenPf);
        tester.assertEqual(result.code, 1, 'File with invalid service action should fail');
        tester.assertIncludes(result.stdout, 'start', 'Error should suggest valid actions');
    });

    // ==========================================
    // SECTION 2: Dry Run Mode
    // ==========================================
    console.log('\n--- Section 2: Dry Run Mode ---');

    await tester.test('Prune with --dry-run flag', async () => {
        const validPf = `
task valid
  describe Valid task
  shell echo "hello"
end
`;
        const result = await tester.runPfCommand(['prune', '--dry-run'], validPf);
        tester.assertEqual(result.code, 0, '--dry-run should work with valid file');
    });

    await tester.test('Prune with -d flag', async () => {
        const validPf = `
task valid
  describe Valid task
  shell echo "hello"
end
`;
        const result = await tester.runPfCommand(['prune', '-d'], validPf);
        tester.assertEqual(result.code, 0, '-d should work with valid file');
    });

    // ==========================================
    // SECTION 3: Verbose Mode
    // ==========================================
    console.log('\n--- Section 3: Verbose Mode ---');

    await tester.test('Prune with --verbose flag', async () => {
        const brokenPf = `
task broken
  describe Broken task
  if $var === "value"
    shell echo "hello"
  end
end
`;
        const result = await tester.runPfCommand(['prune', '--verbose'], brokenPf);
        tester.assertEqual(result.code, 1, 'Verbose mode should detect errors');
        tester.assertIncludes(result.stdout, 'Hint:', 'Verbose should include hints');
    });

    await tester.test('Prune with -v flag', async () => {
        const brokenPf = `
task broken
  describe Broken task
`;
        const result = await tester.runPfCommand(['prune', '-v'], brokenPf);
        tester.assertEqual(result.code, 1, '-v should detect errors');
    });

    // ==========================================
    // SECTION 4: Debug Mode
    // ==========================================
    console.log('\n--- Section 4: Debug Mode ---');

    await tester.test('Debug mode on command', async () => {
        const result = await tester.runPfCommand(['debug-on']);
        tester.assertEqual(result.code, 0, 'debug-on should succeed');
        tester.assertIncludes(result.stdout, 'enabled', 'Should confirm debug enabled');
    });

    await tester.test('Debug mode off command', async () => {
        const result = await tester.runPfCommand(['debug-off']);
        tester.assertEqual(result.code, 0, 'debug-off should succeed');
        tester.assertIncludes(result.stdout, 'disabled', 'Should confirm debug disabled');
    });

    // ==========================================
    // SECTION 5: Output File
    // ==========================================
    console.log('\n--- Section 5: Output File ---');

    await tester.test('Prune creates pfail.fail.pf on error', async () => {
        const brokenPf = `
task broken
  describe Broken task
`;
        const result = await tester.runPfCommand(['prune'], brokenPf);
        tester.assertEqual(result.code, 1, 'Should fail');
        tester.assertIncludes(result.stdout, 'pfail.fail.pf', 'Should mention output file');
    });

    // ==========================================
    // SECTION 6: Valid Syntax Cases
    // ==========================================
    console.log('\n--- Section 6: Valid Syntax Cases ---');

    await tester.test('Valid task with if/else passes', async () => {
        const validPf = `
task valid
  describe Valid task
  if $mode == "dev"
    shell echo "development"
  else
    shell echo "production"
  end
end
`;
        const result = await tester.runPfCommand(['prune'], validPf);
        tester.assertEqual(result.code, 0, 'Valid if/else should pass');
    });

    await tester.test('Valid task with for loop passes', async () => {
        const validPf = `
task valid
  describe Valid task
  for item in ["a", "b", "c"]
    shell echo $item
  end
end
`;
        const result = await tester.runPfCommand(['prune'], validPf);
        tester.assertEqual(result.code, 0, 'Valid for loop should pass');
    });

    await tester.test('Valid task with packages install passes', async () => {
        const validPf = `
task valid
  describe Valid task
  packages install gcc make
end
`;
        const result = await tester.runPfCommand(['prune'], validPf);
        tester.assertEqual(result.code, 0, 'Valid packages install should pass');
    });

    await tester.test('Valid task with service start passes', async () => {
        const validPf = `
task valid
  describe Valid task
  service start nginx
end
`;
        const result = await tester.runPfCommand(['prune'], validPf);
        tester.assertEqual(result.code, 0, 'Valid service start should pass');
    });

    await tester.test('Multiple valid tasks pass', async () => {
        const validPf = `
task task1
  describe First task
  shell echo "one"
end

task task2
  describe Second task
  shell echo "two"
end

task task3
  describe Third task
  shell echo "three"
end
`;
        const result = await tester.runPfCommand(['prune'], validPf);
        tester.assertEqual(result.code, 0, 'Multiple valid tasks should pass');
        tester.assertIncludes(result.stdout, 'Passed:', 'Should show passed count');
    });

    // Print summary
    console.log('\n=============================');
    console.log('📊 Test Results');
    console.log('=============================');
    console.log(`✅ Passed: ${tester.passed}`);
    console.log(`❌ Failed: ${tester.failed}`);
    console.log(`📈 Success Rate: ${Math.round((tester.passed / (tester.passed + tester.failed)) * 100)}%`);

    if (tester.failed === 0) {
        console.log('\n🎉 All prune tests passed!');
    } else {
        console.log('\n⚠️  Some tests failed. Please review the implementation.');
    }

    return tester.failed === 0;
}

// Run tests if executed directly
if (import.meta.url === `file://${process.argv[1]}`) {
    runTests().then(success => {
        process.exit(success ? 0 : 1);
    }).catch(error => {
        console.error('Test runner error:', error);
        process.exit(1);
    });
}

export { runTests, PruneTester };
