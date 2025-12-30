#!/usr/bin/env node

/**
 * Build Status Collector for CI/CD Review
 * Validates build functionality and reports status
 */

import fs from 'fs';
import path from 'path';
import { spawn } from 'child_process';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

class BuildStatusCollector {
    constructor(rootPath = path.resolve(__dirname, '../..')) {
        this.rootPath = rootPath;
        this.buildSteps = {
            nodeSetup: {
                command: 'node',
                args: ['--version'],
                description: 'Node.js Environment Check',
                required: true
            },
            npmInstall: {
                command: 'npm',
                args: ['install', '--silent'],
                description: 'NPM Dependencies Installation',
                required: true
            },
            buildValidation: {
                command: 'npm',
                args: ['run', 'build'],
                description: 'Build Validation',
                required: true
            }
        };
    }

    async runBuildStep(stepName, config) {
        return new Promise((resolve) => {
            console.log(`🔨 Running ${config.description}...`);
            
            const startTime = Date.now();
            const childProcess = spawn(config.command, config.args, {
                cwd: this.rootPath,
                stdio: 'pipe',
                env: { ...process.env, NODE_ENV: 'production' }
            });

            let stdout = '';
            let stderr = '';

            childProcess.stdout.on('data', (data) => {
                stdout += data.toString();
            });

            childProcess.stderr.on('data', (data) => {
                stderr += data.toString();
            });

            childProcess.on('close', (code) => {
                const endTime = Date.now();
                const duration = endTime - startTime;

                resolve({
                    stepName,
                    description: config.description,
                    exitCode: code,
                    success: code === 0,
                    required: config.required,
                    duration,
                    stdout,
                    stderr,
                    timestamp: new Date().toISOString()
                });
            });

            childProcess.on('error', (error) => {
                resolve({
                    stepName,
                    description: config.description,
                    exitCode: -1,
                    success: false,
                    required: config.required,
                    duration: Date.now() - startTime,
                    stdout,
                    stderr: error.message,
                    timestamp: new Date().toISOString(),
                    error: error.message
                });
            });

            // Set timeout for long-running builds
            setTimeout(() => {
                childProcess.kill('SIGTERM');
                resolve({
                    stepName,
                    description: config.description,
                    exitCode: -1,
                    success: false,
                    required: config.required,
                    duration: 60000,
                    stdout,
                    stderr: stderr + '\nBuild step timed out after 60 seconds',
                    timestamp: new Date().toISOString(),
                    timedOut: true
                });
            }, 60000);
        });
    }

    async checkBuildEnvironment() {
        const environment = {
            node: { available: false, version: null },
            npm: { available: false, version: null },
            python: { available: false, version: null },
            packageJson: { exists: false, valid: false },
            buildScripts: { exists: false, scripts: [] }
        };

        // Check Node.js
        try {
            const nodeResult = await this.runCommand('node', ['--version']);
            if (nodeResult.success) {
                environment.node.available = true;
                environment.node.version = nodeResult.stdout.trim();
            }
        } catch (error) {
            console.warn('Node.js not available:', error.message);
        }

        // Check NPM
        try {
            const npmResult = await this.runCommand('npm', ['--version']);
            if (npmResult.success) {
                environment.npm.available = true;
                environment.npm.version = npmResult.stdout.trim();
            }
        } catch (error) {
            console.warn('NPM not available:', error.message);
        }

        // Check package.json
        const packageJsonPath = path.join(this.rootPath, 'package.json');
        if (fs.existsSync(packageJsonPath)) {
            environment.packageJson.exists = true;
            try {
                const packageData = JSON.parse(fs.readFileSync(packageJsonPath, 'utf8'));
                environment.packageJson.valid = true;
                environment.buildScripts.scripts = Object.keys(packageData.scripts || {});
                environment.buildScripts.exists = environment.buildScripts.scripts.length > 0;
            } catch (error) {
                console.warn('Invalid package.json:', error.message);
            }
        }

        return environment;
    }

    async runCommand(command, args) {
        return new Promise((resolve) => {
            const childProcess = spawn(command, args, {
                cwd: this.rootPath,
                stdio: 'pipe'
            });

            let stdout = '';
            let stderr = '';

            childProcess.stdout.on('data', (data) => {
                stdout += data.toString();
            });

            childProcess.stderr.on('data', (data) => {
                stderr += data.toString();
            });

            childProcess.on('close', (code) => {
                resolve({
                    success: code === 0,
                    exitCode: code,
                    stdout,
                    stderr
                });
            });

            childProcess.on('error', (error) => {
                resolve({
                    success: false,
                    exitCode: -1,
                    stdout,
                    stderr: error.message,
                    error: error.message
                });
            });
        });
    }

    async collectBuildStatus() {
        console.log('🔍 Checking build environment...');
        const environment = await this.checkBuildEnvironment();
        
        console.log('🔨 Running build steps...');
        const buildResults = [];
        
        // Run each build step
        for (const [stepName, config] of Object.entries(this.buildSteps)) {
            try {
                const result = await this.runBuildStep(stepName, config);
                buildResults.push(result);
                
                // Stop if required step fails
                if (!result.success && config.required) {
                    console.log(`❌ Required build step '${stepName}' failed, stopping build process`);
                    break;
                }
            } catch (error) {
                console.warn(`Warning: Could not run build step ${stepName}: ${error.message}`);
                buildResults.push({
                    stepName,
                    description: config.description,
                    success: false,
                    required: config.required,
                    duration: 0,
                    timestamp: new Date().toISOString(),
                    error: error.message
                });
            }
        }

        return {
            environment,
            buildResults,
            summary: this.calculateBuildSummary(buildResults, environment)
        };
    }

    calculateBuildSummary(buildResults, environment) {
        const summary = {
            overallSuccess: true,
            totalSteps: buildResults.length,
            successfulSteps: buildResults.filter(r => r.success).length,
            failedSteps: buildResults.filter(r => !r.success).length,
            requiredStepsFailed: buildResults.filter(r => !r.success && r.required).length,
            totalDuration: buildResults.reduce((sum, r) => sum + (r.duration || 0), 0),
            environmentReady: environment.node.available && environment.npm.available && environment.packageJson.exists,
            buildCapable: environment.buildScripts.exists
        };

        // Overall success depends on required steps
        summary.overallSuccess = summary.requiredStepsFailed === 0 && summary.environmentReady;

        return summary;
    }

    generateReport(buildStatusResults) {
        const report = {
            timestamp: new Date().toISOString(),
            summary: buildStatusResults.summary,
            environment: buildStatusResults.environment,
            buildResults: buildStatusResults.buildResults,
            recommendations: this.generateRecommendations(buildStatusResults)
        };

        return report;
    }

    generateRecommendations(results) {
        const recommendations = [];

        // Check for failed build steps
        const failedSteps = results.buildResults.filter(r => !r.success);
        if (failedSteps.length > 0) {
            recommendations.push({
                type: 'build-failures',
                priority: 'high',
                message: `${failedSteps.length} build steps are failing`,
                steps: failedSteps.map(s => s.stepName)
            });
        }

        // Check for missing environment components
        if (!results.environment.node.available) {
            recommendations.push({
                type: 'environment',
                priority: 'high',
                message: 'Node.js is not available - required for build process'
            });
        }

        if (!results.environment.npm.available) {
            recommendations.push({
                type: 'environment',
                priority: 'high',
                message: 'NPM is not available - required for dependency management'
            });
        }

        if (!results.environment.packageJson.exists) {
            recommendations.push({
                type: 'configuration',
                priority: 'medium',
                message: 'package.json file is missing - required for Node.js projects'
            });
        }

        return recommendations;
    }

    formatForCICD(buildStatusResults) {
        let output = "## Build Status\n\n";
        
        // Overall status
        const overallStatus = buildStatusResults.summary.overallSuccess ? 'success' : 'failed';
        output += `**Overall Status:** ${overallStatus}\n\n`;
        
        // Build details
        output += "### Build Details:\n\n";
        
        // Environment check
        if (buildStatusResults.environment.node.available) {
            output += `Node.js build: ✅ Success\n`;
        } else {
            output += `Node.js build: ❌ Failed\n`;
        }

        output += "\n";
        return output;
    }
}

// CLI usage
if (import.meta.url === `file://${process.argv[1]}`) {
    const collector = new BuildStatusCollector();
    
    console.log('🔨 Collecting build status...');
    
    try {
        const results = await collector.collectBuildStatus();
        
        if (process.argv.includes('--cicd')) {
            console.log(collector.formatForCICD(results));
        } else {
            console.log('\n📊 Build Status Summary:');
            console.log(`Overall success: ${results.summary.overallSuccess ? '✅' : '❌'}`);
            console.log(`Build steps: ${results.summary.successfulSteps}/${results.summary.totalSteps} successful`);
        }
    } catch (error) {
        console.error('❌ Error during build status collection:', error.message);
        process.exit(1);
    }
}

export default BuildStatusCollector;