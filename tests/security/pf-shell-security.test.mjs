#!/usr/bin/env node
/**
 * Security Tests for pf_shell.py
 * 
 * Tests the security improvements made to prevent command injection
 * and ensure proper input sanitization.
 */

import { spawn } from 'child_process';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const projectRoot = join(__dirname, '../..');
const pfRunnerDir = join(projectRoot, 'pf-runner');

// Test utilities
class SecurityTester {
    constructor() {
        this.passed = 0;
        this.failed = 0;
        this.tests = [];
    }

    /**
     * Test if pf_shell properly validates commands
     */
    async testCommandValidation(testName, command, shouldPass = true) {
        console.log(`\n🔒 Testing: ${testName}`);
        console.log(`   Command: ${command}`);
        
        return new Promise((resolve) => {
            // Escape the command for Python
            const escapedCommand = command.replace(/\\/g, '\\\\').replace(/"/g, '\\"');
            const proc = spawn('python3', ['-c', `
import sys
sys.path.insert(0, '${pfRunnerDir}')
from pf_shell import validate_shell_syntax

cmd = "${escapedCommand}"
is_valid, error = validate_shell_syntax(cmd)
if is_valid:
    print("VALID")
    sys.exit(0)
else:
    print(f"INVALID: {error}")
    sys.exit(1)
`], {
                stdio: ['pipe', 'pipe', 'pipe'],
                timeout: 5000
            });

            let stdout = '';
            let stderr = '';

            proc.stdout.on('data', (data) => {
                stdout += data.toString();
            });

            proc.stderr.on('data', (data) => {
                stderr += data.toString();
            });

            proc.on('close', (code) => {
                const passed = shouldPass ? (code === 0) : (code !== 0);
                
                if (passed) {
                    console.log(`   ✅ PASS: Validation worked as expected`);
                    this.passed++;
                } else {
                    console.log(`   ❌ FAIL: Expected ${shouldPass ? 'valid' : 'invalid'}, got ${code === 0 ? 'valid' : 'invalid'}`);
                    if (stderr) console.log(`   Error: ${stderr}`);
                    this.failed++;
                }
                
                this.tests.push({ name: testName, passed });
                resolve(passed);
            });

            proc.on('error', (error) => {
                console.log(`   ❌ FAIL: Process error - ${error.message}`);
                this.failed++;
                this.tests.push({ name: testName, passed: false });
                resolve(false);
            });
        });
    }

    /**
     * Test if shell metacharacter detection works
     */
    async testMetacharacterDetection(testName, command, shouldHaveMetachars) {
        console.log(`\n🔍 Testing: ${testName}`);
        console.log(`   Command: ${command}`);
        
        return new Promise((resolve) => {
            // Escape the command for Python
            const escapedCommand = command.replace(/\\/g, '\\\\').replace(/"/g, '\\"');
            const proc = spawn('python3', ['-c', `
import sys
sys.path.insert(0, '${pfRunnerDir}')
from pf_shell import _has_shell_metacharacters

cmd = "${escapedCommand}"
has_metachars = _has_shell_metacharacters(cmd)
print("HAS_METACHARS" if has_metachars else "NO_METACHARS")
sys.exit(0 if has_metachars else 1)
`], {
                stdio: ['pipe', 'pipe', 'pipe'],
                timeout: 5000
            });

            let stdout = '';

            proc.stdout.on('data', (data) => {
                stdout += data.toString();
            });

            proc.on('close', (code) => {
                const hasMetachars = code === 0;
                const passed = hasMetachars === shouldHaveMetachars;
                
                if (passed) {
                    console.log(`   ✅ PASS: Detection worked correctly (${hasMetachars ? 'has' : 'no'} metacharacters)`);
                    this.passed++;
                } else {
                    console.log(`   ❌ FAIL: Expected ${shouldHaveMetachars ? 'metacharacters' : 'no metacharacters'}, got ${hasMetachars ? 'metacharacters' : 'no metacharacters'}`);
                    this.failed++;
                }
                
                this.tests.push({ name: testName, passed });
                resolve(passed);
            });

            proc.on('error', (error) => {
                console.log(`   ❌ FAIL: Process error - ${error.message}`);
                this.failed++;
                this.tests.push({ name: testName, passed: false });
                resolve(false);
            });
        });
    }

    printSummary() {
        console.log('\n' + '='.repeat(60));
        console.log('🔒 Security Test Summary');
        console.log('='.repeat(60));
        console.log(`Total tests: ${this.passed + this.failed}`);
        console.log(`✅ Passed: ${this.passed}`);
        console.log(`❌ Failed: ${this.failed}`);
        console.log('='.repeat(60));
        
        if (this.failed > 0) {
            console.log('\n❌ Some tests failed!');
            process.exit(1);
        } else {
            console.log('\n✅ All security tests passed!');
            process.exit(0);
        }
    }
}

// Main test runner
async function runTests() {
    console.log('🔒 pf_shell.py Security Tests');
    console.log('='.repeat(60));
    console.log('Testing security improvements for command injection prevention');
    
    const tester = new SecurityTester();
    
    // Test command validation
    await tester.testCommandValidation(
        'Simple valid command',
        'echo hello',
        true
    );
    
    await tester.testCommandValidation(
        'Command with environment variable',
        'PATH=/usr/bin echo test',
        true
    );
    
    await tester.testCommandValidation(
        'Empty command after env parsing',
        'VAR=value',
        false
    );
    
    await tester.testCommandValidation(
        'Command with quoted arguments',
        'echo "hello world"',
        true
    );
    
    // Test metacharacter detection
    await tester.testMetacharacterDetection(
        'Simple command (no metacharacters)',
        'echo hello',
        false
    );
    
    await tester.testMetacharacterDetection(
        'Command with pipe (has metacharacters)',
        'echo hello | grep h',
        true
    );
    
    await tester.testMetacharacterDetection(
        'Command with redirect (has metacharacters)',
        'echo hello > output.txt',
        true
    );
    
    await tester.testMetacharacterDetection(
        'Command with variable expansion (has metacharacters)',
        'echo $HOME',
        true
    );
    
    await tester.testMetacharacterDetection(
        'Command with command substitution (has metacharacters)',
        'echo `pwd`',
        true
    );
    
    await tester.testMetacharacterDetection(
        'Command with AND operator (has metacharacters)',
        'make && make test',
        true
    );
    
    tester.printSummary();
}

// Run tests
runTests().catch(err => {
    console.error('Fatal error:', err);
    process.exit(1);
});
