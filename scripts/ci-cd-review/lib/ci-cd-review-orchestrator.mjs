/**
 * CI/CD Review Orchestrator
 * Coordinates all analysis components and generates the final review report.
 */

import fs from 'fs';
import path from 'path';
import FileAnalyzer from './file-analyzer.mjs';
import DocumentationValidator from './documentation-validator.mjs';
import TestCoverageAggregator from './test-coverage-aggregator.mjs';
import BuildStatusCollector from './build-status-collector.mjs';

class CICDReviewOrchestrator {
  constructor(rootPath) {
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
      reviewResults.components.fileAnalysis = { success: false, error: error.message };
    }

    try {
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
      reviewResults.components.documentation = { success: false, error: error.message };
    }

    try {
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
      reviewResults.components.testCoverage = { success: false, error: error.message };
    }

    try {
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
      reviewResults.components.buildStatus = { success: false, error: error.message };
    }

    return reviewResults;
  }

  generateExecutiveSummary(reviewResults) {
    const components = reviewResults.components;
    let summary = 'This comprehensive review covers:\n';

    summary += `- ${components.fileAnalysis?.success ? '✅' : '❌'} Code cleanliness and file size analysis\n`;
    summary += `- ${components.testCoverage?.success ? '✅' : '❌'} Test coverage and Playwright integration\n`;
    summary += `- ${components.documentation?.success ? '✅' : '❌'} Documentation completeness and quality\n`;
    summary += `- ${components.buildStatus?.success ? '✅' : '❌'} Build functionality verification\n`;

    return summary;
  }

  generateActionItems(reviewResults) {
    const actionItems = [];
    const components = reviewResults.components;

    if (components.fileAnalysis?.success && components.fileAnalysis.report?.recommendations?.length > 0) {
      actionItems.push('Review and address code cleanliness issues');
    }
    if (components.testCoverage?.success && components.testCoverage.report?.recommendations?.length > 0) {
      actionItems.push('Fix or improve test coverage');
    }
    if (components.documentation?.success && components.documentation.report?.recommendations?.length > 0) {
      actionItems.push('Update documentation as needed');
    }
    if (!components.buildStatus?.success) {
      actionItems.push('Resolve build issues');
    }
    actionItems.push('Wait for Amazon Q review for additional insights');
    return actionItems;
  }

  formatReviewReport(reviewResults) {
    const timestamp = new Date().toUTCString().replace(/GMT/, 'UTC');

    let report = `# Complete CI/CD Agent Review Report

**Review Date:** ${timestamp}
**Repository:** ${reviewResults.repository}
**Branch:** ${reviewResults.branch}
**Trigger:** ${reviewResults.trigger}

## Executive Summary

${this.generateExecutiveSummary(reviewResults)}

## Detailed Findings

`;

    if (reviewResults.components.buildStatus?.results) {
      report += this.buildStatusCollector.formatForCICD(reviewResults.components.buildStatus.results);
    }
    if (reviewResults.components.fileAnalysis?.results) {
      report += this.fileAnalyzer.formatForCICD(reviewResults.components.fileAnalysis.results);
    }
    if (reviewResults.components.documentation?.results) {
      report += this.documentationValidator.formatForCICD(
        reviewResults.components.documentation.results,
        reviewResults.components.documentation.additionalDocs
      );
    }
    if (reviewResults.components.testCoverage?.results) {
      report += this.testCoverageAggregator.formatForCICD(reviewResults.components.testCoverage.results);
    }

    report += `## Action Items Summary

`;

    const actionItems = this.generateActionItems(reviewResults);
    actionItems.forEach((item) => {
      report += `- [ ] ${item}\n`;
    });

    report += `
---
*This issue was automatically generated by the Complete CI/CD Review workflow.*
`;

    return report;
  }

  async saveReportToFile(report, filename = 'CICD_REVIEW_REPORT.md') {
    const reportPath = path.join(this.rootPath, filename);
    fs.writeFileSync(reportPath, report, 'utf8');
    console.log(`📄 Review report saved to: ${filename}`);
    return reportPath;
  }
}

export default CICDReviewOrchestrator;

