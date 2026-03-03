#!/usr/bin/env node

/**
 * CI/CD Review Orchestrator
 * Main orchestrator that coordinates all analysis components and generates the final review report
 */

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import FileAnalyzer from './file-analyzer.mjs';
import DocumentationValidator from './documentation-validator.mjs';
import TestCoverageAggregator from './test-coverage-aggregator.mjs';
import BuildStatusCollector from './build-status-collector.mjs';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

class CICDReviewOrchestrator {
    constructor(rootPath = path.resolve(__dirname, '../..')) {
        this.rootPath = rootPath;
        this.fileAnalyzer = new FileAnalyzer(rootPath);
        this.documentationValidator = new DocumentationValidator(rootPath);
        this.testCoverageAggregator = new TestCoverageAggregator(rootPath);
        this.buildStatusCollector = new BuildStatusCollector(rootPath);
    }

    async runCompleteReview() {
        console.log('🚀 Starting Complete CI/CD Review...');
        console.log(`📁 Repository: ${path.basename(this.rootPath)}`);
        console.log(`📅 Review Date: ${new Date().toISOString()}`);
        console.log('');

        const reviewResults = {
            timestamp: new Date().toISOString(),
            repository: path.basename(this.rootPath),
            branch: 'main',
            trigger: 'push',
            components: {}
        };

        try {
            // Run file analysis
            console.log('🔍 Running code cleanliness analysis...');
            const fileAnalysisResults = await this.fileAnalyzer.scanDirectory();
            reviewResults.components.fileAnalysis = {
                success: true,
                results: fileAnalysisResults,
                report: this.fileAnalyzer.generateReport(fileAnalysisResults)
            };
            console.log('✅ Code cleanliness analysis completed');
        } catch (error) {
            console.error('❌ File analysis failed:', error.message);
            reviewResults.components.fileAnalysis = {
                success: false,
                error: error.message
            };
        }

        try {
            // Run documentation validation
            console.log('📚 Running documentation analysis...');
            const docValidationResults = await this.documentationValidator.validateDocumentationStructure();
            const additionalDocs = await this.documentationValidator.scanAdditionalDocs();
            reviewResults.components.documentation = {
                success: true,
                results: docValidationResults,
                additionalDocs: additionalDocs,
                report: this.documentationValidator.generateReport(docValidationResults, additionalDocs)
            };
            console.log('✅ Documentation analysis completed');
        } catch (error) {
            console.error('❌ Documentation validation failed:', error.message);
            reviewResults.components.documentation = {
                success: false,
                error: error.message
            };
        }

        try {
            // Run test coverage aggregation
            console.log('🧪 Running test coverage analysis...');
            const testCoverageResults = await this.testCoverageAggregator.aggregateTestCoverage();
            reviewResults.components.testCoverage = {
                success: true,
                results: testCoverageResults,
                report: this.testCoverageAggregator.generateReport(testCoverageResults)
            };
            console.log('✅ Test coverage analysis completed');
        } catch (error) {
            console.error('❌ Test coverage aggregation failed:', error.message);
            reviewResults.components.testCoverage = {
                success: false,
                error: error.message
            };
        }

        try {
            // Run build status collection
            console.log('🔨 Running build functionality verification...');
            const buildStatusResults = await this.buildStatusCollector.collectBuildStatus();
            reviewResults.components.buildStatus = {
                success: buildStatusResults.summary.overallSuccess,
                results: buildStatusResults,
                report: this.buildStatusCollector.generateReport(buildStatusResults)
            };
            console.log('✅ Build functionality verification completed');
        } catch (error) {
            console.error('❌ Build status collection failed:', error.message);
            reviewResults.components.buildStatus = {
                success: false,
                error: error.message
            };
        }

        console.log('');
        console.log('📊 Generating comprehensive review report...');
        
        return reviewResults;
    }

    generateExecutiveSummary(reviewResults) {
        const components = reviewResults.components;
        let summary = "This comprehensive review covers:\n";
        
        // Check each component
        const codeCleanlinessStatus = components.fileAnalysis?.success ? '✅' : '❌';
        summary += `- ${codeCleanlinessStatus} Code cleanliness and file size analysis\n`;
        
        const testCoverageStatus = components.testCoverage?.success ? '✅' : '❌';
        summary += `- ${testCoverageStatus} Test coverage and Playwright integration\n`;
        
        const documentationStatus = components.documentation?.success ? '✅' : '❌';
        summary += `- ${documentationStatus} Documentation completeness and quality\n`;
        
        const buildStatus = components.buildStatus?.success ? '✅' : '❌';
        summary += `- ${buildStatus} Build functionality verification\n`;

        return summary;
    }

    generateActionItems(reviewResults) {
        const actionItems = [];
        const components = reviewResults.components;

        // File analysis action items
        if (components.fileAnalysis?.success && components.fileAnalysis.report?.recommendations?.length > 0) {
            const highPriorityFileIssues = components.fileAnalysis.report.recommendations.filter(r => r.priority === 'high');
            if (highPriorityFileIssues.length > 0) {
                actionItems.push('Review and address code cleanliness issues');
            }
        }

        // Test coverage action items
        if (components.testCoverage?.success && components.testCoverage.report?.recommendations?.length > 0) {
            const testIssues = components.testCoverage.report.recommendations.filter(r => r.priority === 'high');
            if (testIssues.length > 0) {
                actionItems.push('Fix or improve test coverage');
            }
        }

        // Documentation action items
        if (components.documentation?.success && components.documentation.report?.recommendations?.length > 0) {
            const docIssues = components.documentation.report.recommendations.filter(r => r.priority === 'high');
            if (docIssues.length > 0) {
                actionItems.push('Update documentation as needed');
            }
        }

        // Build action items
        if (!components.buildStatus?.success) {
            actionItems.push('Resolve build issues');
        }

        // Always add Amazon Q review item
        actionItems.push('Wait for Amazon Q review for additional insights');

        return actionItems;
    }

    formatReviewReport(reviewResults) {
        const timestamp = new Date().toUTCString().replace(/GMT/, 'UTC');
        
        let report = `# Complete CI/CD Agent Review Report

**Review Date:** ${timestamp}
**Repository:** P4X-ng/pf-web-poly-compile-helper-runner
**Branch:** ${reviewResults.branch}
**Trigger:** ${reviewResults.trigger}

## Executive Summary

${this.generateExecutiveSummary(reviewResults)}

## Detailed Findings

`;

        // Add build status section
        if (reviewResults.components.buildStatus?.success !== undefined) {
            report += this.buildStatusCollector.formatForCICD(reviewResults.components.buildStatus.results);
        } else {
            report += `## Build Status

**Overall Status:** failed

### Build Details:

Build verification: ❌ Failed

`;
        }

        // Add code cleanliness section
        if (reviewResults.components.fileAnalysis?.success) {
            report += this.fileAnalyzer.formatForCICD(reviewResults.components.fileAnalysis.results);
        } else {
            report += `## Code Cleanliness Analysis

❌ Code cleanliness analysis failed to complete

`;
        }

        // Add documentation section
        if (reviewResults.components.documentation?.success) {
            report += this.documentationValidator.formatForCICD(
                reviewResults.components.documentation.results,
                reviewResults.components.documentation.additionalDocs
            );
        } else {
            report += `## Documentation Analysis

❌ Documentation analysis failed to complete

`;
        }

        // Add test coverage section (optional, not in original template but good to have)
        if (reviewResults.components.testCoverage?.success) {
            report += this.testCoverageAggregator.formatForCICD(reviewResults.components.testCoverage.results);
        }

        // Add next steps and action items
        report += `## Next Steps - Amazon Q Review

After reviewing these GitHub Copilot agent findings, Amazon Q will provide additional insights:
- Security analysis
- Performance optimization opportunities
- AWS best practices
- Enterprise architecture patterns

## Action Items Summary

`;

        const actionItems = this.generateActionItems(reviewResults);
        actionItems.forEach(item => {
            report += `- [ ] ${item}\n`;
        });

        report += `
---
*This issue was automatically generated by the Complete CI/CD Review workflow.*
*Amazon Q review will follow automatically.*
`;

        return report;
    }

    async saveReportToFile(report, filename = 'CICD_REVIEW_REPORT.md') {
        const reportPath = path.join(this.rootPath, filename);
        
        try {
            fs.writeFileSync(reportPath, report, 'utf8');
            console.log(`📄 Review report saved to: ${filename}`);
            return reportPath;
        } catch (error) {
            console.error(`❌ Failed to save report to ${filename}:`, error.message);
            throw error;
        }
    }
}

// CLI usage
if (import.meta.url === `file://${process.argv[1]}`) {
    const orchestrator = new CICDReviewOrchestrator();
    
    try {
        const reviewResults = await orchestrator.runCompleteReview();
        const report = orchestrator.formatReviewReport(reviewResults);
        
        if (process.argv.includes('--save')) {
            await orchestrator.saveReportToFile(report);
        }
        
        if (process.argv.includes('--json')) {
            console.log(JSON.stringify(reviewResults, null, 2));
        } else {
            console.log('\n' + '='.repeat(80));
            console.log('📋 COMPLETE CI/CD REVIEW REPORT');
            console.log('='.repeat(80));
            console.log(report);
        }
        
        // Exit with appropriate code
        const hasFailures = Object.values(reviewResults.components).some(component => !component.success);
        process.exit(hasFailures ? 1 : 0);
        
    } catch (error) {
        console.error('❌ CI/CD Review failed:', error.message);
        process.exit(1);
    }
}

export default CICDReviewOrchestrator;