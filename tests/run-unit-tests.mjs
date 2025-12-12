#!/usr/bin/env node
/**
 * Master Test Runner for pf Unit Tests
 * 
 * Runs all unit test suites and generates a comprehensive report
 */

import { spawn } from 'child_process';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const projectRoot = join(__dirname, '..');

// Test suite definitions
const testSuites = [
    {
        name: 'Grammar Tests',
        file: 'grammar/grammar.test.mjs',
        description: 'Tests grammar constructs and syntax validation'
    },
    {
        name: 'Parser Tests',
        file: 'grammar/parser.test.mjs',
        description: 'Tests variable interpolation and task parsing'
    },
    {
        name: 'Polyglot Tests',
        file: 'shell-scripts/polyglot.test.mjs',
        description: 'Tests shell language support and polyglot execution'
    },
    {
        name: 'Build Helper Tests',
        file: 'compilation/build-helpers.test.mjs',
        description: 'Tests build system integrations'
    },
    {
        name: 'Containerization Tests',
        file: 'containerization/containerization.test.mjs',
        description: 'Tests automatic containerization and Quadlet generation'
    },
    {
        name: 'Sync & Ops Tests',
        file: 'debugging/sync-ops.test.mjs',
        description: 'Tests sync, service, and package operations'
    },
    {
        name: 'API Server Tests',
        file: 'api/api-server.test.mjs',
        description: 'Tests REST API endpoints'
    },
    {
        name: 'Checksec Tests',
        file: 'checksec.test.mjs',
        description: 'Tests binary security analysis tool'
    },
    {
        name: 'Security Tools Tests',
        file: 'security-tools.test.mjs',
        description: 'Tests security tool integrations'
    },
    {
        name: 'Package Manager Tests',
        file: 'package-manager/package-manager.test.mjs',
        description: 'Tests package format translation tool'
    },
    {
        name: 'pf Tasks Validation Tests',
        file: 'pf-tasks-validation.test.mjs',
        description: 'Tests that all pf tasks are syntactically correct and properly documented'
    }
];

// ANSI colors
const colors = {
    reset: '\x1b[0m',
    bright: '\x1b[1m',
    red: '\x1b[31m',
    green: '\x1b[32m',
    yellow: '\x1b[33m',
    blue: '\x1b[34m',
    magenta: '\x1b[35m',
    cyan: '\x1b[36m'
};

function log(color, prefix, message) {
    console.log(`${color}${prefix}${colors.reset} ${message}`);
}

async function runTestSuite(suite) {
    const testFile = join(__dirname, suite.file);
    
    return new Promise((resolve) => {
        log(colors.blue, '[RUNNING]', `${suite.name} (${suite.file})`);
        
        const proc = spawn('node', [testFile], {
            cwd: projectRoot,
            stdio: ['pipe', 'pipe', 'pipe'],
            timeout: 120000 // 2 minute timeout
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
            // Parse results from output
            const passMatch = stdout.match(/Passed:\s*(\d+)/);
            const failMatch = stdout.match(/Failed:\s*(\d+)/);
            
            const passed = passMatch ? parseInt(passMatch[1]) : 0;
            const failed = failMatch ? parseInt(failMatch[1]) : (code !== 0 ? 1 : 0);
            
            resolve({
                name: suite.name,
                file: suite.file,
                description: suite.description,
                passed,
                failed,
                exitCode: code,
                stdout,
                stderr,
                success: code === 0 && failed === 0
            });
        });

        proc.on('error', (error) => {
            resolve({
                name: suite.name,
                file: suite.file,
                description: suite.description,
                passed: 0,
                failed: 1,
                exitCode: 1,
                stdout: '',
                stderr: error.message,
                success: false,
                error: error.message
            });
        });
    });
}

async function runAllTests(options = {}) {
    const startTime = Date.now();
    const results = [];
    
    console.log(`\n${colors.bright}╔════════════════════════════════════════════════════════════════╗${colors.reset}`);
    console.log(`${colors.bright}║          pf Language Unit Test Suite                            ║${colors.reset}`);
    console.log(`${colors.bright}╚════════════════════════════════════════════════════════════════╝${colors.reset}\n`);
    
    console.log(`${colors.cyan}Running ${testSuites.length} test suites...${colors.reset}\n`);
    
    // Filter suites if specific ones are requested
    let suitesToRun = testSuites;
    if (options.filter) {
        suitesToRun = testSuites.filter(s => 
            s.name.toLowerCase().includes(options.filter.toLowerCase()) ||
            s.file.toLowerCase().includes(options.filter.toLowerCase())
        );
    }
    
    // Run each test suite
    for (const suite of suitesToRun) {
        try {
            const result = await runTestSuite(suite);
            results.push(result);
            
            if (result.success) {
                log(colors.green, '[PASS]', `${suite.name}: ${result.passed} passed`);
            } else {
                log(colors.red, '[FAIL]', `${suite.name}: ${result.passed} passed, ${result.failed} failed`);
            }
            
            if (options.verbose && (result.failed > 0 || !result.success)) {
                console.log(`\n${colors.yellow}--- Output ---${colors.reset}`);
                console.log(result.stdout);
                if (result.stderr) {
                    console.log(`${colors.red}--- Errors ---${colors.reset}`);
                    console.log(result.stderr);
                }
                console.log(`${colors.yellow}--- End ---${colors.reset}\n`);
            }
        } catch (error) {
            results.push({
                name: suite.name,
                file: suite.file,
                passed: 0,
                failed: 1,
                success: false,
                error: error.message
            });
            log(colors.red, '[ERROR]', `${suite.name}: ${error.message}`);
        }
    }
    
    const endTime = Date.now();
    const duration = ((endTime - startTime) / 1000).toFixed(2);
    
    // Calculate totals
    const totalPassed = results.reduce((sum, r) => sum + r.passed, 0);
    const totalFailed = results.reduce((sum, r) => sum + r.failed, 0);
    const totalTests = totalPassed + totalFailed;
    const successRate = totalTests > 0 ? Math.round((totalPassed / totalTests) * 100) : 0;
    
    const suitesPass = results.filter(r => r.success).length;
    const suitesFail = results.filter(r => !r.success).length;
    
    // Print summary
    console.log(`\n${colors.bright}╔════════════════════════════════════════════════════════════════╗${colors.reset}`);
    console.log(`${colors.bright}║                    Test Summary                                  ║${colors.reset}`);
    console.log(`${colors.bright}╚════════════════════════════════════════════════════════════════╝${colors.reset}\n`);
    
    console.log(`${colors.cyan}Test Suites:${colors.reset}`);
    console.log(`  ${colors.green}✓ Passed:${colors.reset} ${suitesPass}`);
    console.log(`  ${colors.red}✗ Failed:${colors.reset} ${suitesFail}`);
    console.log(`  ${colors.blue}Total:${colors.reset} ${results.length}`);
    
    console.log(`\n${colors.cyan}Individual Tests:${colors.reset}`);
    console.log(`  ${colors.green}✓ Passed:${colors.reset} ${totalPassed}`);
    console.log(`  ${colors.red}✗ Failed:${colors.reset} ${totalFailed}`);
    console.log(`  ${colors.blue}Total:${colors.reset} ${totalTests}`);
    console.log(`  ${colors.magenta}Success Rate:${colors.reset} ${successRate}%`);
    
    console.log(`\n${colors.cyan}Duration:${colors.reset} ${duration}s`);
    
    // List failed suites
    if (suitesFail > 0) {
        console.log(`\n${colors.red}Failed Suites:${colors.reset}`);
        results.filter(r => !r.success).forEach(r => {
            console.log(`  ✗ ${r.name} (${r.file})`);
            if (r.error) {
                console.log(`    Error: ${r.error}`);
            }
        });
    }
    
    // Overall result
    console.log('');
    if (suitesFail === 0) {
        console.log(`${colors.green}${colors.bright}🎉 All test suites passed!${colors.reset}`);
    } else {
        console.log(`${colors.red}${colors.bright}⚠️  Some test suites failed. Please review the results above.${colors.reset}`);
    }
    
    return {
        suites: results,
        totalPassed,
        totalFailed,
        totalTests,
        successRate,
        suitesPass,
        suitesFail,
        duration,
        success: suitesFail === 0
    };
}

// Parse command line arguments
function parseArgs() {
    const args = process.argv.slice(2);
    const options = {
        verbose: false,
        filter: null,
        help: false
    };
    
    for (let i = 0; i < args.length; i++) {
        const arg = args[i];
        if (arg === '-v' || arg === '--verbose') {
            options.verbose = true;
        } else if (arg === '-f' || arg === '--filter') {
            options.filter = args[++i];
        } else if (arg === '-h' || arg === '--help') {
            options.help = true;
        }
    }
    
    return options;
}

function printHelp() {
    console.log(`
${colors.bright}pf Unit Test Runner${colors.reset}

Usage: node run-unit-tests.mjs [options]

Options:
  -v, --verbose     Show detailed output for failed tests
  -f, --filter      Filter test suites by name (e.g., -f grammar)
  -h, --help        Show this help message

Available Test Suites:
${testSuites.map(s => `  • ${s.name.padEnd(25)} ${s.description}`).join('\n')}
`);
}

// Run tests if executed directly
if (import.meta.url === `file://${process.argv[1]}`) {
    const options = parseArgs();
    
    if (options.help) {
        printHelp();
        process.exit(0);
    }
    
    runAllTests(options).then(result => {
        process.exit(result.success ? 0 : 1);
    }).catch(error => {
        console.error('Test runner error:', error);
        process.exit(1);
    });
}

export { runAllTests, testSuites };
