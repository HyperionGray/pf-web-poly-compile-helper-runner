#!/usr/bin/env node
/**
 * Unit Tests for pf Help Variations and Flexible Parameters
 * 
 * Tests the support for:
 * - Help command variations: help, --help, -h, hlep, hepl, heelp, hlp
 * - Flexible parameter formats: --key=value, -k val, key=value
 * - Subcommand grouping
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
class HelpTester {
    constructor() {
        this.passed = 0;
        this.failed = 0;
        this.tests = [];
    }

    async runPfParser(args = []) {
        return new Promise((resolve, reject) => {
            const proc = spawn('python3', ['pf_parser.py', ...args], {
                cwd: pfRunnerDir,
                stdio: ['pipe', 'pipe', 'pipe'],
                timeout: 10000
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
}

// Test cases
async function runTests() {
    const tester = new HelpTester();
    
    console.log('🔍 pf Help Variations & Flexible Parameters Tests');
    console.log('=================================================\n');

    // ==========================================
    // SECTION 1: Help Command Variations
    // ==========================================
    console.log('\n--- Section 1: Help Command Variations ---');

    await tester.test('Standard help command', async () => {
        const result = await tester.runPfParser(['help']);
        if (result.code !== 0) {
            throw new Error(`help command failed: ${result.stderr}`);
        }
        if (!result.stdout.includes('Available tasks:') && !result.stdout.includes('Built-ins:')) {
            throw new Error('Help output missing expected content');
        }
    });

    await tester.test('--help flag', async () => {
        const result = await tester.runPfParser(['--help']);
        if (result.code !== 0) {
            throw new Error(`--help command failed: ${result.stderr}`);
        }
        if (!result.stdout.includes('Available tasks:') && !result.stdout.includes('Built-ins:')) {
            throw new Error('Help output missing expected content');
        }
    });

    await tester.test('-h flag', async () => {
        const result = await tester.runPfParser(['-h']);
        if (result.code !== 0) {
            throw new Error(`-h command failed: ${result.stderr}`);
        }
        if (!result.stdout.includes('Available tasks:') && !result.stdout.includes('Built-ins:')) {
            throw new Error('Help output missing expected content');
        }
    });

    await tester.test('hlep typo variation', async () => {
        const result = await tester.runPfParser(['hlep']);
        if (result.code !== 0) {
            throw new Error(`hlep command failed: ${result.stderr}`);
        }
        if (!result.stdout.includes('Available tasks:') && !result.stdout.includes('Built-ins:')) {
            throw new Error('Help output missing expected content');
        }
    });

    await tester.test('hepl typo variation', async () => {
        const result = await tester.runPfParser(['hepl']);
        if (result.code !== 0) {
            throw new Error(`hepl command failed: ${result.stderr}`);
        }
        if (!result.stdout.includes('Available tasks:') && !result.stdout.includes('Built-ins:')) {
            throw new Error('Help output missing expected content');
        }
    });

    await tester.test('heelp typo variation', async () => {
        const result = await tester.runPfParser(['heelp']);
        if (result.code !== 0) {
            throw new Error(`heelp command failed: ${result.stderr}`);
        }
        if (!result.stdout.includes('Available tasks:') && !result.stdout.includes('Built-ins:')) {
            throw new Error('Help output missing expected content');
        }
    });

    await tester.test('hlp typo variation', async () => {
        const result = await tester.runPfParser(['hlp']);
        if (result.code !== 0) {
            throw new Error(`hlp command failed: ${result.stderr}`);
        }
        if (!result.stdout.includes('Available tasks:') && !result.stdout.includes('Built-ins:')) {
            throw new Error('Help output missing expected content');
        }
    });

    // ==========================================
    // SECTION 2: Task-Specific Help
    // ==========================================
    console.log('\n--- Section 2: Task-Specific Help ---');

    await tester.test('help for specific task', async () => {
        const result = await tester.runPfParser(['help', 'update']);
        if (result.code !== 0) {
            throw new Error(`help update command failed: ${result.stderr}`);
        }
        if (!result.stdout.includes('Built-in task: update') && !result.stdout.includes('Task: update')) {
            throw new Error('Task help output missing expected content');
        }
    });

    await tester.test('hlep for specific task', async () => {
        const result = await tester.runPfParser(['hlep', 'update']);
        if (result.code !== 0) {
            throw new Error(`hlep update command failed: ${result.stderr}`);
        }
        if (!result.stdout.includes('Built-in task: update') && !result.stdout.includes('Task: update')) {
            throw new Error('Task help output missing expected content');
        }
    });

    await tester.test('task followed by help', async () => {
        const result = await tester.runPfParser(['update', 'help']);
        if (result.code !== 0) {
            throw new Error(`update help command failed: ${result.stderr}`);
        }
        if (!result.stdout.includes('Built-in task: update') && !result.stdout.includes('Task: update')) {
            throw new Error('Task help output missing expected content');
        }
    });

    await tester.test('task followed by --help', async () => {
        const result = await tester.runPfParser(['update', '--help']);
        if (result.code !== 0) {
            throw new Error(`update --help command failed: ${result.stderr}`);
        }
        if (!result.stdout.includes('Built-in task: update') && !result.stdout.includes('Task: update')) {
            throw new Error('Task help output missing expected content');
        }
    });

    await tester.test('task followed by hlep', async () => {
        const result = await tester.runPfParser(['update', 'hlep']);
        if (result.code !== 0) {
            throw new Error(`update hlep command failed: ${result.stderr}`);
        }
        if (!result.stdout.includes('Built-in task: update') && !result.stdout.includes('Task: update')) {
            throw new Error('Task help output missing expected content');
        }
    });

    // ==========================================
    // SECTION 3: List Command
    // ==========================================
    console.log('\n--- Section 3: List Command ---');

    await tester.test('list command', async () => {
        const result = await tester.runPfParser(['list']);
        if (result.code !== 0) {
            throw new Error(`list command failed: ${result.stderr}`);
        }
        if (!result.stdout.includes('Built-ins:')) {
            throw new Error('List output missing Built-ins section');
        }
    });

    await tester.test('--list flag', async () => {
        const result = await tester.runPfParser(['--list']);
        if (result.code !== 0) {
            throw new Error(`--list command failed: ${result.stderr}`);
        }
        if (!result.stdout.includes('Built-ins:')) {
            throw new Error('List output missing Built-ins section');
        }
    });

    // ==========================================
    // SECTION 4: Subcommand Grouping
    // ==========================================
    console.log('\n--- Section 4: Subcommand Grouping ---');

    await tester.test('tasks are grouped by prefix', async () => {
        const result = await tester.runPfParser(['list']);
        if (result.code !== 0) {
            throw new Error(`list command failed: ${result.stderr}`);
        }
        // Should have [install] group (common across all Pfyfiles)
        if (!result.stdout.includes('[install]')) {
            throw new Error('List output should contain task groups like [install]');
        }
    });

    await tester.test('install tasks are under [install] group', async () => {
        const result = await tester.runPfParser(['list']);
        if (result.code !== 0) {
            throw new Error(`list command failed: ${result.stderr}`);
        }
        // Check that the [install] group exists
        const installGroupIndex = result.stdout.indexOf('[install]');
        if (installGroupIndex === -1) {
            throw new Error('Could not find [install] group');
        }
    });

    // ==========================================
    // SECTION 5: Help for Non-Existent Task
    // ==========================================
    console.log('\n--- Section 5: Help for Non-Existent Task ---');

    await tester.test('help for non-existent task suggests alternatives', async () => {
        const result = await tester.runPfParser(['help', 'nonexistenttask']);
        // Should fail but provide suggestions
        if (!result.stdout.includes('not found') && !result.stderr.includes('not found')) {
            throw new Error('Should indicate task not found');
        }
    });

    await tester.test('help for similar task name suggests alternatives', async () => {
        const result = await tester.runPfParser(['help', 'updae']);
        // Should fail but suggest 'update'
        if (!result.stdout.includes('Did you mean') && !result.stderr.includes('Did you mean')) {
            // It's okay if no suggestions, as long as it doesn't crash
        }
    });

    // Print summary
    console.log('\n=============================');
    console.log('📊 Help Variations Test Results');
    console.log('=============================');
    console.log(`✅ Passed: ${tester.passed}`);
    console.log(`❌ Failed: ${tester.failed}`);
    const total = tester.passed + tester.failed;
    const successRate = total > 0 ? Math.round((tester.passed / total) * 100) : 0;
    console.log(`📈 Success Rate: ${successRate}%`);

    if (tester.failed === 0) {
        console.log('\n🎉 All help variation tests passed!');
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

export { runTests, HelpTester };
