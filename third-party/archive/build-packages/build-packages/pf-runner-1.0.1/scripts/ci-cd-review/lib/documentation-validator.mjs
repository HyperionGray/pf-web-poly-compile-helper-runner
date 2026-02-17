/**
 * Documentation Validator for CI/CD Review
 * Validates documentation completeness and quality.
 */

import fs from 'fs';
import path from 'path';

function countWords(text) {
  return (text || '')
    .replace(/[`*_>#-]/g, ' ')
    .replace(/\s+/g, ' ')
    .trim()
    .split(' ')
    .filter(Boolean).length;
}

class DocumentationValidator {
  constructor(rootPath) {
    this.rootPath = rootPath;

    this.requiredRootDocs = ['README.md', 'LICENSE'];
    this.requiredDocsStructure = {
      'docs/CHANGELOG.md': 'changelog',
      'docs/QUICKSTART.md': 'quick start guide',
      'docs/LICENSE.md': 'license text (markdown)',
      'docs/development/CONTRIBUTING.md': 'contributing guidelines',
      'docs/development/CODE_OF_CONDUCT.md': 'code of conduct',
      'docs/security/SECURITY.md': 'security policy',
      'docs/installation/INSTALL.md': 'installation guide'
    };
    this.requiredReadmeSections = ['Installation', 'Usage', 'Features', 'Contributing', 'License', 'Documentation', 'Examples', 'API'];
  }

  async validateDocumentationStructure() {
    const results = {
      rootDocumentation: {},
      docsDirectory: {},
      readmeAnalysis: {},
      summary: { totalRequired: 0, totalFound: 0, missingFiles: [], extraFiles: [] }
    };

    for (const docFile of this.requiredRootDocs) {
      const filePath = path.join(this.rootPath, docFile);
      const exists = fs.existsSync(filePath);

      results.rootDocumentation[docFile] = { exists, path: filePath, wordCount: 0, status: exists ? '✅' : '❌' };
      results.summary.totalRequired++;

      if (exists) {
        results.summary.totalFound++;
        try {
          results.rootDocumentation[docFile].wordCount = countWords(fs.readFileSync(filePath, 'utf8'));
        } catch (error) {
          console.warn(`Warning: Could not read ${docFile}: ${error.message}`);
        }
      } else {
        results.summary.missingFiles.push(docFile);
      }
    }

    for (const [docPath, description] of Object.entries(this.requiredDocsStructure)) {
      const fullPath = path.join(this.rootPath, docPath);
      const exists = fs.existsSync(fullPath);

      results.docsDirectory[docPath] = { exists, description, path: fullPath, wordCount: 0, status: exists ? '✅' : '❌' };
      results.summary.totalRequired++;

      if (exists) {
        results.summary.totalFound++;
        try {
          results.docsDirectory[docPath].wordCount = countWords(fs.readFileSync(fullPath, 'utf8'));
        } catch (error) {
          console.warn(`Warning: Could not read ${docPath}: ${error.message}`);
        }
      } else {
        results.summary.missingFiles.push(docPath);
      }
    }

    const readmePath = path.join(this.rootPath, 'README.md');
    results.readmeAnalysis = fs.existsSync(readmePath)
      ? await this.analyzeReadmeContent(readmePath)
      : { sections: {}, missingSection: this.requiredReadmeSections, totalSections: 0, requiredSections: this.requiredReadmeSections.length };

    return results;
  }

  async analyzeReadmeContent(readmePath) {
    const content = fs.readFileSync(readmePath, 'utf8');
    const lines = content.split('\n');

    const analysis = {
      sections: {},
      missingSection: [],
      totalSections: 0,
      requiredSections: this.requiredReadmeSections.length,
      wordCount: countWords(content)
    };

    const sectionRegex = /^#+\s+(.+)$/;
    const foundSections = new Set();
    for (const line of lines) {
      const match = line.match(sectionRegex);
      if (!match) continue;
      foundSections.add(match[1].trim());
      analysis.totalSections++;
    }

    for (const requiredSection of this.requiredReadmeSections) {
      const found = Array.from(foundSections).some((s) => s.toLowerCase().includes(requiredSection.toLowerCase()));
      analysis.sections[requiredSection] = { found, status: found ? '✅' : '❌' };
      if (!found) analysis.missingSection.push(requiredSection);
    }

    return analysis;
  }

  async scanAdditionalDocs() {
    const docsPath = path.join(this.rootPath, 'docs');
    const additionalDocs = [];
    if (!fs.existsSync(docsPath)) return additionalDocs;

    const scanRecursive = (dirPath, relativePath = '') => {
      let items;
      try {
        items = fs.readdirSync(dirPath);
      } catch (error) {
        console.warn(`Warning: Could not scan directory ${dirPath}: ${error.message}`);
        return;
      }

      for (const item of items) {
        const itemPath = path.join(dirPath, item);
        const itemRelativePath = path.join(relativePath, item);

        let stat;
        try {
          stat = fs.statSync(itemPath);
        } catch (error) {
          console.warn(`Warning: Could not stat ${itemPath}: ${error.message}`);
          continue;
        }

        if (stat.isDirectory()) {
          scanRecursive(itemPath, itemRelativePath);
          continue;
        }
        if (!stat.isFile() || !item.endsWith('.md')) continue;

        const fullRelativePath = path.join('docs', itemRelativePath);
        if (this.requiredDocsStructure[fullRelativePath]) continue;

        try {
          const content = fs.readFileSync(itemPath, 'utf8');
          additionalDocs.push({ path: fullRelativePath, wordCount: countWords(content), size: stat.size });
        } catch (error) {
          console.warn(`Warning: Could not read ${fullRelativePath}: ${error.message}`);
        }
      }
    };

    scanRecursive(docsPath);
    return additionalDocs;
  }

  generateReport(validationResults, additionalDocs = []) {
    const summary = {
      requiredCompletionRate:
        validationResults.summary.totalRequired > 0
          ? Math.round((validationResults.summary.totalFound / validationResults.summary.totalRequired) * 100)
          : 0,
      readmeCompletenessRate:
        validationResults.readmeAnalysis.requiredSections > 0
          ? Math.round(
              ((validationResults.readmeAnalysis.requiredSections - validationResults.readmeAnalysis.missingSection.length) /
                validationResults.readmeAnalysis.requiredSections) *
                100
            )
          : 0,
      additionalDocsCount: additionalDocs.length
    };

    const recommendations = [];
    if (validationResults.summary.missingFiles.length > 0) {
      recommendations.push({
        type: 'missing-docs',
        priority: 'high',
        message: `Add missing required documentation files (${validationResults.summary.missingFiles.length})`,
        files: validationResults.summary.missingFiles
      });
    }
    if (validationResults.readmeAnalysis.missingSection?.length > 0) {
      recommendations.push({
        type: 'readme-sections',
        priority: 'medium',
        message: `README.md missing ${validationResults.readmeAnalysis.missingSection.length} required sections`,
        sections: validationResults.readmeAnalysis.missingSection
      });
    }

    const veryShort = additionalDocs.filter((d) => d.wordCount < 50);
    if (veryShort.length > 0) {
      recommendations.push({
        type: 'short-docs',
        priority: 'low',
        message: `${veryShort.length} documentation files are very short (<50 words)`,
        files: veryShort.slice(0, 20).map((d) => d.path)
      });
    }

    return {
      timestamp: new Date().toISOString(),
      summary,
      required: validationResults,
      additionalDocs,
      recommendations
    };
  }

  formatForCICD(validationResults, additionalDocs = []) {
    const report = this.generateReport(validationResults, additionalDocs);
    let output = '## Documentation Analysis\n\n';

    output += '### Essential Documentation Files:\n';
    output += '#### Root Documentation:\n';
    for (const [name, info] of Object.entries(validationResults.rootDocumentation)) {
      output += `${info.status} ${name} (${info.wordCount} words)\n`;
    }

    output += '\n#### Documentation in docs/:\n';
    for (const [docPath, info] of Object.entries(validationResults.docsDirectory)) {
      output += `${info.status} ${docPath} (${info.wordCount} words)\n`;
    }

    output += '\n### README.md Content Check:\n';
    for (const [section, info] of Object.entries(validationResults.readmeAnalysis.sections || {})) {
      output += `${info.status} Contains '${section}' section\n`;
    }

    output += '\n### Documentation Summary:\n';
    output += `- **Completion Rate**: ${report.summary.requiredCompletionRate}% (${validationResults.summary.totalFound}/${validationResults.summary.totalRequired} required files)\n`;
    output += `- **README Completeness**: ${report.summary.readmeCompletenessRate}% (${validationResults.readmeAnalysis.requiredSections - validationResults.readmeAnalysis.missingSection.length}/${validationResults.readmeAnalysis.requiredSections} required sections)\n`;
    output += `- **Additional Documentation**: ${report.summary.additionalDocsCount} extra documentation files found\n`;

    if (report.recommendations.length > 0) {
      output += '\n### Documentation Recommendations:\n';
      report.recommendations.forEach((rec) => {
        output += `- **${rec.priority.toUpperCase()}**: ${rec.message}\n`;
      });
    }

    output += '\n';
    return output;
  }
}

export default DocumentationValidator;

