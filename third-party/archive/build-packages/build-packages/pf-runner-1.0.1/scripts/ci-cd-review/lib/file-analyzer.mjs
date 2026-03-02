/**
 * File Analyzer for CI/CD Review
 * Analyzes repository files for size, type, and categorization.
 */

import fs from 'fs';
import path from 'path';

class FileAnalyzer {
  constructor(rootPath) {
    this.rootPath = rootPath;
    this.excludePatterns = [
      /node_modules/,
      /\.git/,
      /\.vscode/,
      /\.idea/,
      /dist/,
      /build/,
      /coverage/,
      /playwright-report/,
      /test-results/,
      /\.pyc$/,
      /\.pyo$/,
      /__pycache__/,
      /\.o$/,
      /\.so$/,
      /\.dylib$/,
      /\.dll$/,
      /\.exe$/,
      /\.bin$/,
      /\.tar/,
      /\.gz$/,
      /\.zip$/,
      /\.7z$/,
      /\.rar$/,
      /\.png$/,
      /\.jpg$/,
      /\.jpeg$/,
      /\.gif$/,
      /\.svg$/,
      /\.ico$/,
      /\.woff/,
      /\.ttf$/,
      /\.eot$/
    ];
    this.largeFileThreshold = 500; // lines
  }

  shouldExclude(filePath) {
    const relativePath = path.relative(this.rootPath, filePath);
    return this.excludePatterns.some((pattern) => pattern.test(relativePath));
  }

  countLines(filePath) {
    try {
      const content = fs.readFileSync(filePath, 'utf8');
      return content.split('\n').length;
    } catch (error) {
      console.warn(`Warning: Could not read file ${filePath}: ${error.message}`);
      return 0;
    }
  }

  categorizeFile(filePath) {
    const ext = path.extname(filePath).toLowerCase();
    const basename = path.basename(filePath).toLowerCase();
    const relativePath = path.relative(this.rootPath, filePath);

    if (basename.includes('grammar') && ext === '.py') return 'auto-generated';
    if (basename.includes('parser') || basename.includes('main') || basename.includes('core')) return 'core-component';
    if (relativePath.includes('test') || basename.includes('test') || basename.includes('spec')) return 'test';
    if (ext === '.md' || basename.includes('readme') || basename.includes('doc')) return 'documentation';
    if (basename.includes('config') || ['.json', '.yml', '.yaml', '.toml'].includes(ext)) return 'configuration';
    if (basename.includes('build') || basename.includes('deploy') || basename.includes('docker') || basename.includes('makefile')) {
      return 'build-deployment';
    }
    return 'source-code';
  }

  async scanDirectory(dirPath = this.rootPath) {
    const results = {
      totalFiles: 0,
      largeFiles: [],
      filesByCategory: {},
      summary: {
        totalLines: 0,
        largeFileCount: 0,
        categories: {}
      }
    };

    const scanRecursive = (currentPath) => {
      let items;
      try {
        items = fs.readdirSync(currentPath);
      } catch (error) {
        console.warn(`Warning: Could not scan directory ${currentPath}: ${error.message}`);
        return;
      }

      for (const item of items) {
        const itemPath = path.join(currentPath, item);
        if (this.shouldExclude(itemPath)) continue;

        let stat;
        try {
          stat = fs.statSync(itemPath);
        } catch (error) {
          console.warn(`Warning: Could not stat ${itemPath}: ${error.message}`);
          continue;
        }

        if (stat.isDirectory()) {
          scanRecursive(itemPath);
          continue;
        }
        if (!stat.isFile()) continue;

        results.totalFiles++;
        const lineCount = this.countLines(itemPath);
        const category = this.categorizeFile(itemPath);
        const relativePath = path.relative(this.rootPath, itemPath);

        results.summary.totalLines += lineCount;

        if (!results.filesByCategory[category]) {
          results.filesByCategory[category] = [];
          results.summary.categories[category] = { count: 0, totalLines: 0 };
        }

        results.filesByCategory[category].push({ path: relativePath, lines: lineCount, size: stat.size });
        results.summary.categories[category].count++;
        results.summary.categories[category].totalLines += lineCount;

        if (lineCount > this.largeFileThreshold) {
          results.largeFiles.push({ path: relativePath, lines: lineCount, category, size: stat.size });
          results.summary.largeFileCount++;
        }
      }
    };

    scanRecursive(dirPath);
    results.largeFiles.sort((a, b) => b.lines - a.lines);
    return results;
  }

  generateRecommendations(results) {
    const recommendations = [];

    const veryLargeFiles = results.largeFiles.filter((f) => f.lines > 2000);
    if (veryLargeFiles.length > 0) {
      recommendations.push({
        type: 'code-organization',
        priority: 'medium',
        message: `Consider refactoring ${veryLargeFiles.length} very large files (>2000 lines) for better maintainability`,
        files: veryLargeFiles.map((f) => f.path)
      });
    }

    const largeSourceFiles = results.largeFiles.filter((f) => f.category === 'source-code');
    if (largeSourceFiles.length > 5) {
      recommendations.push({
        type: 'architecture',
        priority: 'low',
        message: `Consider modularizing ${largeSourceFiles.length} large source code files`,
        files: largeSourceFiles.map((f) => f.path)
      });
    }

    const largeAutoGenerated = results.largeFiles.filter((f) => f.category === 'auto-generated');
    if (largeAutoGenerated.length > 0) {
      recommendations.push({
        type: 'build-optimization',
        priority: 'low',
        message: `${largeAutoGenerated.length} large auto-generated files detected - consider build optimization`,
        files: largeAutoGenerated.map((f) => f.path)
      });
    }

    return recommendations;
  }

  generateReport(analysisResults) {
    return {
      timestamp: new Date().toISOString(),
      summary: analysisResults.summary,
      largeFiles: analysisResults.largeFiles,
      recommendations: this.generateRecommendations(analysisResults)
    };
  }

  formatForCICD(analysisResults) {
    const report = this.generateReport(analysisResults);
    let output = '## Code Cleanliness Analysis\n\n';

    if (report.largeFiles.length > 0) {
      output += '### Large Files (>500 lines):\n';
      report.largeFiles.forEach((file) => {
        output += `${file.lines} lines: ./${file.path}\n`;
      });
      output += '\n';
    } else {
      output += '### Large Files (>500 lines):\n';
      output += '✅ No files exceed 500 lines threshold\n\n';
    }

    output += '### File Category Breakdown:\n';
    Object.entries(report.summary.categories).forEach(([category, stats]) => {
      output += `**${category.replace('-', ' ').toUpperCase()}**: ${stats.count} files, ${stats.totalLines} total lines\n`;
    });
    output += '\n';

    if (report.recommendations.length > 0) {
      output += '### Recommendations:\n';
      report.recommendations.forEach((rec) => {
        output += `- **${rec.priority.toUpperCase()}**: ${rec.message}\n`;
      });
      output += '\n';
    }

    return output;
  }
}

export default FileAnalyzer;

