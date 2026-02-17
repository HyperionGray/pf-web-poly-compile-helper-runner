/**
 * Build Status Collector for CI/CD Review
 * Validates build functionality and reports status.
 */

import fs from 'fs';
import path from 'path';
import { runCommand } from './spawn-utils.mjs';

class BuildStatusCollector {
  constructor(rootPath) {
    this.rootPath = rootPath;
    this.buildSteps = {
      nodeSetup: { command: 'node', args: ['--version'], description: 'Node.js Environment Check', required: true },
      npmInstall: { command: 'npm', args: ['install', '--silent'], description: 'NPM Dependencies Installation', required: true },
      buildValidation: { command: 'npm', args: ['run', 'build'], description: 'Build Validation', required: true }
    };
  }

  async checkBuildEnvironment() {
    const environment = {
      node: { available: false, version: null },
      npm: { available: false, version: null },
      packageJson: { exists: false, valid: false },
      buildScripts: { exists: false, scripts: [] }
    };

    const nodeResult = await runCommand('node', ['--version'], { cwd: this.rootPath, timeoutMs: 5000 });
    if (nodeResult.success) {
      environment.node.available = true;
      environment.node.version = nodeResult.stdout.trim();
    }

    const npmResult = await runCommand('npm', ['--version'], { cwd: this.rootPath, timeoutMs: 5000 });
    if (npmResult.success) {
      environment.npm.available = true;
      environment.npm.version = npmResult.stdout.trim();
    }

    const packageJsonPath = path.join(this.rootPath, 'package.json');
    if (fs.existsSync(packageJsonPath)) {
      environment.packageJson.exists = true;
      try {
        const packageData = JSON.parse(fs.readFileSync(packageJsonPath, 'utf8'));
        environment.packageJson.valid = true;
        environment.buildScripts.scripts = Object.keys(packageData.scripts || {});
        environment.buildScripts.exists = environment.buildScripts.scripts.length > 0;
      } catch {
        // ignore
      }
    }

    return environment;
  }

  async runBuildStep(stepName, config) {
    console.log(`🔨 Running ${config.description}...`);
    const res = await runCommand(config.command, config.args, { cwd: this.rootPath, timeoutMs: 60000 });
    return {
      stepName,
      description: config.description,
      exitCode: res.exitCode,
      success: res.success,
      required: config.required,
      duration: res.durationMs,
      stdout: res.stdout,
      stderr: res.stderr,
      timestamp: new Date().toISOString(),
      timedOut: !!res.timedOut
    };
  }

  calculateBuildSummary(buildResults, environment) {
    const summary = {
      overallSuccess: true,
      totalSteps: buildResults.length,
      successfulSteps: buildResults.filter((r) => r.success).length,
      failedSteps: buildResults.filter((r) => !r.success).length,
      requiredStepsFailed: buildResults.filter((r) => !r.success && r.required).length,
      totalDuration: buildResults.reduce((sum, r) => sum + (r.duration || 0), 0),
      environmentReady: environment.node.available && environment.npm.available && environment.packageJson.exists,
      buildCapable: environment.buildScripts.exists
    };

    summary.overallSuccess = summary.requiredStepsFailed === 0 && summary.environmentReady;
    return summary;
  }

  async collectBuildStatus() {
    console.log('🔍 Checking build environment...');
    const environment = await this.checkBuildEnvironment();

    console.log('🔨 Running build steps...');
    const buildResults = [];

    for (const [stepName, config] of Object.entries(this.buildSteps)) {
      const result = await this.runBuildStep(stepName, config);
      buildResults.push(result);
      if (!result.success && config.required) {
        console.log(`❌ Required build step '${stepName}' failed, stopping build process`);
        break;
      }
    }

    return { environment, buildResults, summary: this.calculateBuildSummary(buildResults, environment) };
  }

  generateReport(buildStatusResults) {
    return { timestamp: new Date().toISOString(), summary: buildStatusResults.summary, environment: buildStatusResults.environment, steps: buildStatusResults.buildResults };
  }

  formatForCICD(buildStatusResults) {
    const report = this.generateReport(buildStatusResults);
    const overallStatus = report.summary.overallSuccess ? 'success' : 'failed';
    let output = '## Build Status\n\n';
    output += `**Overall Status:** ${overallStatus}\n\n`;
    output += '### Build Details:\n\n';
    output += `Node.js build: ${report.summary.overallSuccess ? '✅ Success' : '❌ Failed'}\n\n`;
    return output;
  }
}

export default BuildStatusCollector;

