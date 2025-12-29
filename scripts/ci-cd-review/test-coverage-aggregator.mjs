#!/usr/bin/env node

/**
 * Test Coverage Aggregator for CI/CD Review
 * Aggregates test results from Playwright and unit tests
 */

import fs from 'fs';
import path from 'path';
import { spawn } from 'child_process';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

class TestCoverageAggregator {
    constructor(rootPath = path.resolve(__dirname, '../..')) {
        this.rootPath = rootPath;
        this.testTypes = {
            playwright: {
                command: 'npm',
                args: ['run', 'test'],
                description: 'Playwright E2E Tests'
            },
            unit: {
                command: 'npm',
                args: ['run', 'test:unit'],
                description: 'Unit Tests'
            },
            tui: {
                command: 'npm',
                args: ['run', 'test:tui'],
                description: 'TUI Tests'
            },
            grammar: {
                command: 'npm',
                args: ['run', 'test:grammar'],
                description: 'Grammar Tests'
            },
            api: {
                command: 'npm',
                args: ['run', 'test:api'],
                description: 'API Tests'
            }
        };
    }

    async runTestSuite(testType, config) {
        return new Promise((resolve) => {
            console.log(`🧪 Running ${config.description}...`);
            
            const startTime = Date.now();
            const process = spawn(config.command, config.args, {
                cwd: this.rootPath,
                stdio: 'pipe',
                env: { ...process.env, CI: 'true' }
            });

            let stdout = '';
            let stderr = '';

            process.stdout.on('data', (data) => {
                stdout += data.toString();
            });

            process.stderr.on('data', (data) => {
                stderr += data.toString();
            });

            process.on('close', (code) => {
                const endTime = Date.now();
                const duration = endTime - startTime;

                resolve({
                    testType,
                    description: config.description,
                    exitCode: code,
                    success: code === 0,
                    duration,
                    stdout,
                    stderr,
                    timestamp: new Date().toISOString()
                });
            });

            // Set timeout for long-running tests
            setTimeout(() => {
                process.kill('SIGTERM');
                resolve({
                    testType,
                    description: config.description,
                    exitCode: -1,
                    success: false,
                    duration: 30000,
                    stdout,
                    stderr: stderr + '\nTest timed out after 30 seconds',
                    timestamp: new Date().toISOString(),
                    timedOut: true
                });
            }, 30000);
        });
    }

    parseTestResults(result) {
        const parsed = {
            testType: result.testType,
            description: result.description,
            success: result.success,
            duration: result.duration,
            timestamp: result.timestamp,
            stats: {
                total: 0,
                passed: 0,
                failed: 0,
                skipped: 0
            },
            details: []
        };

        // Parse Playwright results
        if (result.testType === 'playwright') {
            const playwrightMatch = result.stdout.match(/(\d+) passed.*?(\d+) failed.*?(\d+) skipped/);
            if (playwrightMatch) {
                parsed.stats.passed = parseInt(playwrightMatch[1]) || 0;
                parsed.stats.failed = parseInt(playwrightMatch[2]) || 0;
                parsed.stats.skipped = parseInt(playwrightMatch[3]) || 0;
                parsed.stats.total = parsed.stats.passed + parsed.stats.failed + parsed.stats.skipped;
            }
        }

        // Parse Node.js test results (for unit tests)
        if (result.testType === 'unit' || result.testType === 'tui' || result.testType === 'grammar' || result.testType === 'api') {
            // Look for test completion indicators
            const testLines = result.stdout.split('\n').filter(line => 
                line.includes('✓') || line.includes('✗') || line.includes('PASS') || line.includes('FAIL')
            );
            
            parsed.stats.total = testLines.length;
            parsed.stats.passed = testLines.filter(line => 
                line.includes('✓') || line.includes('PASS')
            ).length;
            parsed.stats.failed = testLines.filter(line => 
                line.includes('✗') || line.includes('FAIL')
            ).length;
        }

        // Extract error details if failed
        if (!result.success && result.stderr) {
            parsed.details.push({
                type: 'error',
                message: result.stderr.split('\n').slice(0, 5).join('\n') // First 5 lines of error
            });
        }

        return parsed;
    }

    async scanTestFiles() {
        const testFiles = {
            playwright: [],
            unit: [],
            other: []
        };

        const scanDirectory = (dirPath, category) => {
            if (!fs.existsSync(dirPath)) return;

            try {
                const items = fs.readdirSync(dirPath, { withFileTypes: true });
                
                for (const item of items) {
                    if (item.isDirectory()) {
                        scanDirectory(path.join(dirPath, item.name), category);
                    } else if (item.isFile()) {
                        const filePath = path.join(dirPath, item.name);
                        const relativePath = path.relative(this.rootPath, filePath);
                        
                        if (item.name.endsWith('.spec.ts') || item.name.endsWith('.spec.js')) {
                            testFiles.playwright.push(relativePath);
                        } else if (item.name.endsWith('.test.mjs') || item.name.endsWith('.test.js')) {
                            testFiles.unit.push(relativePath);
                        } else if (item.name.includes('test') && (item.name.endsWith('.js') || item.name.endsWith('.mjs') || item.name.endsWith('.sh'))) {
                            testFiles.other.push(relativePath);
                        }
                    }
                }
            } catch (error) {
                console.warn(`Warning: Could not scan test directory ${dirPath}: ${error.message}`);
            }
        };

        // Scan tests directory
        scanDirectory(path.join(this.rootPath, 'tests'), 'tests');
        
        // Scan for test files in other locations
        scanDirectory(path.join(this.rootPath, 'pf-runner'), 'pf-runner');

        return testFiles;
    }

    async aggregateTestCoverage() {
        console.log('🔍 Scanning test files...');
        const testFiles = await this.scanTestFiles();
        
        console.log('🧪 Running test suites...');
        const results = [];
        
        // Run each test suite
        for (const [testType, config] of Object.entries(this.testTypes)) {
            try {
                const result = await this.runTestSuite(testType, config);
                const parsed = this.parseTestResults(result);
                results.push(parsed);
            } catch (error) {
                console.warn(`Warning: Could not run ${testType} tests: ${error.message}`);
                results.push({
                    testType,
                    description: config.description,
                    success: false,
                    duration: 0,
                    timestamp: new Date().toISOString(),
                    stats: { total: 0, passed: 0, failed: 0, skipped: 0 },
                    details: [{ type: 'error', message: error.message }]
                });
            }
        }

        return {
            testFiles,
            results,
            summary: this.calculateSummary(results, testFiles)
        };
    }

    calculateSummary(results, testFiles) {
        const summary = {
            totalTestFiles: testFiles.playwright.length + testFiles.unit.length + testFiles.other.length,
            totalTestSuites: results.length,
            successfulSuites: results.filter(r => r.success).length,
            failedSuites: results.filter(r => !r.success).length,
            totalTests: results.reduce((sum, r) => sum + r.stats.total, 0),
            totalPassed: results.reduce((sum, r) => sum + r.stats.passed, 0),
            totalFailed: results.reduce((sum, r) => sum + r.stats.failed, 0),
            totalSkipped: results.reduce((sum, r) => sum + r.stats.skipped, 0),
            totalDuration: results.reduce((sum, r) => sum + r.duration, 0),
            coveragePercentage: 0
        };

        // Calculate coverage percentage
        if (summary.totalTests > 0) {
            summary.coveragePercentage = Math.round((summary.totalPassed / summary.totalTests) * 100);
        }

        return summary;
    }

    generateReport(aggregationResults) {
        const report = {
            timestamp: new Date().toISOString(),
            summary: aggregationResults.summary,
            testFiles: aggregationResults.testFiles,
            results: aggregationResults.results,
            recommendations: this.generateRecommendations(aggregationResults)
        };

        return report;
    }

    generateRecommendations(results) {
        const recommendations = [];

        // Check for failed test suites
        const failedSuites = results.results.filter(r => !r.success);
        if (failedSuites.length > 0) {
            recommendations.push({
                type: 'test-failures',
                priority: 'high',
                message: `${failedSuites.length} test suites are failing`,
                suites: failedSuites.map(s => s.testType)
            });
        }

        // Check for low test coverage
        if (results.summary.coveragePercentage < 80) {
            recommendations.push({
                type: 'test-coverage',
                priority: 'medium',
                message: `Test coverage is ${results.summary.coveragePercentage}% - consider adding more tests`,
                currentCoverage: results.summary.coveragePercentage
            });
        }

        // Check for missing test types
        const hasPlaywright = results.testFiles.playwright.length > 0;
        const hasUnit = results.testFiles.unit.length > 0;
        
        if (!hasPlaywright) {
            recommendations.push({
                type: 'missing-tests',
                priority: 'medium',
                message: 'No Playwright E2E tests found - consider adding integration tests'
            });
        }

        if (!hasUnit) {
            recommendations.push({
                type: 'missing-tests',
                priority: 'medium',
                message: 'No unit tests found - consider adding unit test coverage'
            });
        }

        return recommendations;
    }

    formatForCICD(aggregationResults) {
        const report = this.generateReport(aggregationResults);
        
        let output = "## Test Coverage and Playwright Integration\n\n";
        
        // Overall status
        const overallStatus = report.summary.failedSuites === 0 ? '✅ Success' : '❌ Failed';
        output += `**Overall Test Status:** ${overallStatus}\n\n`;
        
        // Test suite breakdown
        output += "### Test Suite Results:\n";
        report.results.forEach(result => {
            const status = result.success ? '✅' : '❌';
            const duration = Math.round(result.duration / 1000);
            output += `${status} **${result.description}**: ${result.stats.passed}/${result.stats.total} tests passed (${duration}s)\n`;
        });
        
        // Summary statistics
        output += `\n### Test Coverage Summary:\n`;
        output += `- **Total Test Files**: ${report.summary.totalTestFiles}\n`;
        output += `- **Test Suites**: ${report.summary.successfulSuites}/${report.summary.totalTestSuites} passing\n`;
        output += `- **Individual Tests**: ${report.summary.totalPassed}/${report.summary.totalTests} passing (${report.summary.coveragePercentage}%)\n`;
        output += `- **Total Duration**: ${Math.round(report.summary.totalDuration / 1000)}s\n`;

        // File breakdown
        output += `\n### Test File Breakdown:\n`;
        output += `- **Playwright Tests**: ${report.testFiles.playwright.length} files\n`;
        output += `- **Unit Tests**: ${report.testFiles.unit.length} files\n`;
        output += `- **Other Tests**: ${report.testFiles.other.length} files\n`;

        // Add recommendations if any
        if (report.recommendations.length > 0) {
            output += "\n### Test Recommendations:\n";
            report.recommendations.forEach(rec => {
                const priority = rec.priority.toUpperCase();
                output += `- **${priority}**: ${rec.message}\n`;
            });
        }

        output += "\n";
        return output;
    }
}

// CLI usage
if (import.meta.url === `file://${process.argv[1]}`) {
    const aggregator = new TestCoverageAggregator();
    
    console.log('🧪 Aggregating test coverage...');
    
    try {
        const results = await aggregator.aggregateTestCoverage();
        const report = aggregator.generateReport(results);
        
        if (process.argv.includes('--json')) {
            console.log(JSON.stringify(report, null, 2));
        } else if (process.argv.includes('--cicd')) {
            console.log(aggregator.formatForCICD(results));
        } else {
            console.log('\n📊 Test Coverage Summary:');
            console.log(`Test suites: ${report.summary.successfulSuites}/${report.summary.totalTestSuites} passing`);
            console.log(`Individual tests: ${report.summary.totalPassed}/${report.summary.totalTests} passing (${report.summary.coveragePercentage}%)`);
            console.log(`Total test files: ${report.summary.totalTestFiles}`);
            console.log(`Total duration: ${Math.round(report.summary.totalDuration / 1000)}s`);
            
            if (report.recommendations.length > 0) {
                console.log('\n💡 Recommendations:');
                report.recommendations.forEach(rec => {
                    console.log(`  ${rec.priority.toUpperCase()}: ${rec.message}`);
                });
            }
        }
    } catch (error) {
        console.error('❌ Error during test coverage aggregation:', error.message);
        process.exit(1);
    }
}

export default TestCoverageAggregator;