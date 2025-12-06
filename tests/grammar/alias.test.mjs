#!/usr/bin/env node
/**
 * Tests for pf task alias feature
 * 
 * Tests the new [alias name] syntax for defining short command aliases
 */

import { spawn } from 'child_process';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';
import { writeFileSync, unlinkSync, existsSync } from 'fs';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const projectRoot = join(__dirname, '../..');

// Test utilities
let passed = 0;
let failed = 0;

function log(color, prefix, message) {
    const colors = {
        green: '\x1b[32m',
        red: '\x1b[31m',
        yellow: '\x1b[33m',
        reset: '\x1b[0m'
    };
    console.log(`${colors[color] || ''}${prefix}${colors.reset} ${message}`);
}

async function runPfParser(code) {
    return new Promise((resolve, reject) => {
        const proc = spawn('python3', ['-c', code], {
            cwd: join(projectRoot, 'pf-runner'),
            stdio: ['pipe', 'pipe', 'pipe'],
            timeout: 30000
        });

        let stdout = '';
        let stderr = '';

        proc.stdout.on('data', (data) => stdout += data.toString());
        proc.stderr.on('data', (data) => stderr += data.toString());

        proc.on('close', (code) => {
            resolve({ code, stdout, stderr });
        });

        proc.on('error', reject);
    });
}

async function test(name, testFn) {
    try {
        console.log(`\n🧪 Testing: ${name}`);
        await testFn();
        log('green', '✅ PASS:', name);
        passed++;
    } catch (error) {
        log('red', '❌ FAIL:', name);
        console.log(`   Error: ${error.message}`);
        failed++;
    }
}

function assertEqual(actual, expected, message = '') {
    if (JSON.stringify(actual) !== JSON.stringify(expected)) {
        throw new Error(`${message} - Expected ${JSON.stringify(expected)}, got ${JSON.stringify(actual)}`);
    }
}

function assertTrue(condition, message = '') {
    if (!condition) {
        throw new Error(message || 'Assertion failed');
    }
}

// Test cases
async function runTests() {
    console.log('🔍 pf Alias Feature Unit Tests');
    console.log('===============================\n');

    // Test 1: Basic alias parsing
    await test('Parse task with single alias [alias name] format', async () => {
        const result = await runPfParser(`
from pf_parser import _parse_task_definition
name, params, aliases = _parse_task_definition('task long-command [alias cmd]')
print(f'{name}|{aliases}')
        `);
        assertTrue(result.code === 0, `Command failed: ${result.stderr}`);
        assertTrue(result.stdout.includes("long-command|['cmd']"), `Unexpected output: ${result.stdout}`);
    });

    // Test 2: alias= format
    await test('Parse task with [alias=name] format', async () => {
        const result = await runPfParser(`
from pf_parser import _parse_task_definition
name, params, aliases = _parse_task_definition('task long-command [alias=cmd]')
print(f'{name}|{aliases}')
        `);
        assertTrue(result.code === 0, `Command failed: ${result.stderr}`);
        assertTrue(result.stdout.includes("long-command|['cmd']"), `Unexpected output: ${result.stdout}`);
    });

    // Test 3: Multiple aliases
    await test('Parse task with multiple aliases using pipe separator', async () => {
        const result = await runPfParser(`
from pf_parser import _parse_task_definition
name, params, aliases = _parse_task_definition('task long-command [alias cmd|alias=c]')
print(f'{name}|{len(aliases)}')
        `);
        assertTrue(result.code === 0, `Command failed: ${result.stderr}`);
        assertTrue(result.stdout.includes('long-command|2'), `Unexpected output: ${result.stdout}`);
    });

    // Test 4: Alias with parameters
    await test('Parse task with alias and parameters', async () => {
        const result = await runPfParser(`
from pf_parser import _parse_task_definition
name, params, aliases = _parse_task_definition('task long-command [alias cmd] port=8080')
print(f'{name}|{aliases}|{params}')
        `);
        assertTrue(result.code === 0, `Command failed: ${result.stderr}`);
        assertTrue(result.stdout.includes("long-command"), `Missing task name: ${result.stdout}`);
        assertTrue(result.stdout.includes("cmd"), `Missing alias: ${result.stdout}`);
        assertTrue(result.stdout.includes("port"), `Missing param: ${result.stdout}`);
    });

    // Test 5: Task class stores aliases
    await test('Task class stores aliases correctly', async () => {
        const result = await runPfParser(`
from pf_parser import parse_pfyfile_text
text = '''
task my-task [alias mt]
  describe A test task
  shell echo hello
end
'''
tasks = parse_pfyfile_text(text)
print(f'{tasks["my-task"].aliases}')
        `);
        assertTrue(result.code === 0, `Command failed: ${result.stderr}`);
        assertTrue(result.stdout.includes("['mt']"), `Unexpected output: ${result.stdout}`);
    });

    // Test 6: Multiple separate alias blocks
    await test('Parse multiple separate [alias x] blocks', async () => {
        const result = await runPfParser(`
from pf_parser import _parse_task_definition
name, params, aliases = _parse_task_definition('task long-command [alias cmd] [alias=lc]')
print(f'{name}|{sorted(aliases)}')
        `);
        assertTrue(result.code === 0, `Command failed: ${result.stderr}`);
        assertTrue(result.stdout.includes("long-command"), `Missing task name: ${result.stdout}`);
        // Both aliases should be captured
        const output = result.stdout.trim();
        assertTrue(output.includes('cmd'), `Missing alias cmd: ${output}`);
        assertTrue(output.includes('lc'), `Missing alias lc: ${output}`);
    });

    // Test 7: Task without alias (backward compatibility)
    await test('Task without alias still works (backward compatibility)', async () => {
        const result = await runPfParser(`
from pf_parser import _parse_task_definition
name, params, aliases = _parse_task_definition('task simple-task param1=value1')
print(f'{name}|{aliases}|{params}')
        `);
        assertTrue(result.code === 0, `Command failed: ${result.stderr}`);
        assertTrue(result.stdout.includes("simple-task|[]"), `Unexpected output: ${result.stdout}`);
        assertTrue(result.stdout.includes("param1"), `Missing param: ${result.stdout}`);
    });

    // Test 8: REST API Pfyfile aliases load correctly
    await test('REST API Pfyfile aliases load correctly', async () => {
        const result = await runPfParser(`
import sys
sys.path.insert(0, '${join(projectRoot, 'pf-runner')}')
import os
os.chdir('${projectRoot}')
from pf_parser import parse_pfyfile_text

with open('Pfyfile.rest-api.pf', 'r') as f:
    text = f.read()

tasks = parse_pfyfile_text(text)

# Check that rest-on has alias 'ron'
if 'rest-on' in tasks:
    print(f"rest-on aliases: {tasks['rest-on'].aliases}")
else:
    print("ERROR: rest-on not found")
        `);
        assertTrue(result.code === 0, `Command failed: ${result.stderr}`);
        assertTrue(result.stdout.includes("['ron']"), `Unexpected output: ${result.stdout}`);
    });

    // Print summary
    console.log('\n=============================');
    console.log('📊 Alias Test Results');
    console.log('=============================');
    console.log(`✅ Passed: ${passed}`);
    console.log(`❌ Failed: ${failed}`);
    console.log(`📈 Success Rate: ${Math.round((passed / (passed + failed)) * 100)}%`);

    if (failed === 0) {
        console.log('\n🎉 All alias tests passed!');
    } else {
        console.log('\n⚠️  Some tests failed. Please review the implementation.');
    }

    return failed === 0;
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

export { runTests };
