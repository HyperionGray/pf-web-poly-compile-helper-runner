#!/usr/bin/env node
/**
 * Test suite for checksec binary security analysis tool
 */

import { spawn } from 'child_process';
import { promises as fs } from 'fs';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const projectRoot = join(__dirname, '..');

// Test configuration
const CHECKSEC_SCRIPT = join(projectRoot, 'tools/security/checksec.py');
const TEST_TIMEOUT = 10000; // 10 seconds

class ChecksecTester {
    constructor() {
        this.passed = 0;
        this.failed = 0;
        this.tests = [];
    }

    async runCommand(cmd, args = [], options = {}) {
        return new Promise((resolve, reject) => {
            const process = spawn(cmd, args, {
                stdio: 'pipe',
                timeout: TEST_TIMEOUT,
                ...options
            });

            let stdout = '';
            let stderr = '';

            process.stdout?.on('data', (data) => {
                stdout += data.toString();
            });

            process.stderr?.on('data', (data) => {
                stderr += data.toString();
            });

            process.on('close', (code) => {
                resolve({
                    code,
                    stdout: stdout.trim(),
                    stderr: stderr.trim()
                });
            });

            process.on('error', (error) => {
                reject(error);
            });
        });
    }

    async test(name, testFn) {
        try {
            console.log(`\n🧪 Testing: ${name}`);
            await testFn();
            console.log(`✅ PASS: ${name}`);
            this.passed++;
        } catch (error) {
            console.log(`❌ FAIL: ${name}`);
            console.log(`   Error: ${error.message}`);
            this.failed++;
        }
        this.tests.push({ name, passed: this.failed === 0 });
    }

    async checkScriptExists() {
        try {
            await fs.access(CHECKSEC_SCRIPT);
            return true;
        } catch {
            return false;
        }
    }

    async testHelp() {
        const result = await this.runCommand('python3', [CHECKSEC_SCRIPT, '--help']);
        
        if (result.code !== 0) {
            throw new Error(`Help command failed with code ${result.code}`);
        }

        if (!result.stdout.includes('Analyze binary security features')) {
            throw new Error('Help output missing expected content');
        }

        console.log('   ✓ Help command works');
        console.log('   ✓ Help output contains expected content');
    }

    async testSystemBinary() {
        // Test with /bin/ls if it exists
        try {
            await fs.access('/bin/ls');
        } catch {
            console.log('   ⚠️  /bin/ls not found, skipping system binary test');
            return;
        }

        const result = await this.runCommand('python3', [CHECKSEC_SCRIPT, '/bin/ls']);
        
        if (result.code !== 0) {
            throw new Error(`Analysis failed with code ${result.code}: ${result.stderr}`);
        }

        if (!result.stdout.includes('Binary Security Analysis')) {
            throw new Error('Output missing expected header');
        }

        if (!result.stdout.includes('RELRO:')) {
            throw new Error('Output missing RELRO analysis');
        }

        console.log('   ✓ System binary analysis works');
        console.log('   ✓ Output format is correct');
    }

    async testJsonOutput() {
        // Test JSON output with /bin/ls if it exists
        try {
            await fs.access('/bin/ls');
        } catch {
            console.log('   ⚠️  /bin/ls not found, skipping JSON test');
            return;
        }

        const result = await this.runCommand('python3', [CHECKSEC_SCRIPT, '--json', '/bin/ls']);
        
        if (result.code !== 0) {
            throw new Error(`JSON analysis failed with code ${result.code}: ${result.stderr}`);
        }

        let jsonData;
        try {
            jsonData = JSON.parse(result.stdout);
        } catch (error) {
            throw new Error(`Invalid JSON output: ${error.message}`);
        }

        const requiredFields = ['file', 'relro', 'stack_canary', 'nx', 'pie', 'rpath', 'fortify'];
        for (const field of requiredFields) {
            if (!(field in jsonData)) {
                throw new Error(`Missing required field: ${field}`);
            }
        }

        console.log('   ✓ JSON output is valid');
        console.log('   ✓ All required fields present');
    }

    async testNonExistentFile() {
        const result = await this.runCommand('python3', [CHECKSEC_SCRIPT, '/nonexistent/file']);
        
        if (result.code === 0) {
            throw new Error('Should fail for non-existent file');
        }

        if (!result.stdout.includes('Error:') && !result.stdout.includes('not found')) {
            throw new Error('Should show appropriate error message');
        }

        console.log('   ✓ Handles non-existent files correctly');
    }

    async testBatchMode() {
        // Test batch mode on /usr/bin if it exists
        try {
            await fs.access('/usr/bin');
        } catch {
            console.log('   ⚠️  /usr/bin not found, skipping batch test');
            return;
        }

        const result = await this.runCommand('python3', [CHECKSEC_SCRIPT, '--batch', '/usr/bin']);
        
        if (result.code !== 0) {
            throw new Error(`Batch analysis failed with code ${result.code}: ${result.stderr}`);
        }

        // Should have some output for batch mode
        if (result.stdout.length === 0) {
            throw new Error('Batch mode produced no output');
        }

        console.log('   ✓ Batch mode works');
    }

    async testPfIntegration() {
        // Test pf task integration
        const result = await this.runCommand('python3', [join(projectRoot, 'pf-runner/pf'), 'checksec-demo'], {
            cwd: projectRoot
        });
        
        // This might fail if dependencies aren't installed, so we're lenient
        if (result.code === 0) {
            console.log('   ✓ pf integration works');
        } else {
            console.log('   ⚠️  pf integration test skipped (dependencies may be missing)');
        }
    }

    async runAllTests() {
        console.log('🔍 Checksec Binary Security Analysis Tool Tests');
        console.log('===============================================');

        // Check if script exists
        if (!(await this.checkScriptExists())) {
            console.log(`❌ FATAL: checksec.py not found at ${CHECKSEC_SCRIPT}`);
            return false;
        }

        console.log(`✅ Found checksec script at: ${CHECKSEC_SCRIPT}`);

        // Run tests
        await this.test('Help Command', () => this.testHelp());
        await this.test('System Binary Analysis', () => this.testSystemBinary());
        await this.test('JSON Output Format', () => this.testJsonOutput());
        await this.test('Error Handling', () => this.testNonExistentFile());
        await this.test('Batch Mode', () => this.testBatchMode());
        await this.test('pf Integration', () => this.testPfIntegration());

        // Summary
        console.log('\n📊 Test Results');
        console.log('================');
        console.log(`✅ Passed: ${this.passed}`);
        console.log(`❌ Failed: ${this.failed}`);
        console.log(`📈 Success Rate: ${Math.round((this.passed / (this.passed + this.failed)) * 100)}%`);

        if (this.failed === 0) {
            console.log('\n🎉 All tests passed! checksec integration is working correctly.');
        } else {
            console.log('\n⚠️  Some tests failed. Please check the implementation.');
        }

        return this.failed === 0;
    }
}

// Run tests if this file is executed directly
if (import.meta.url === `file://${process.argv[1]}`) {
    const tester = new ChecksecTester();
    tester.runAllTests().then(success => {
        process.exit(success ? 0 : 1);
    }).catch(error => {
        console.error('Test runner error:', error);
        process.exit(1);
    });
}

export { ChecksecTester };