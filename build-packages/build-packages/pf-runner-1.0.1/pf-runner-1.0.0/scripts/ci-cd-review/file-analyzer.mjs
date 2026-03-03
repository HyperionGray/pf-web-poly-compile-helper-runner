#!/usr/bin/env node

/**
 * File Analyzer for CI/CD Review
 * Analyzes repository files for size, type, and categorization
 */

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

class FileAnalyzer {
    constructor(rootPath = path.resolve(__dirname, '../..')) {
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
        return this.excludePatterns.some(pattern => pattern.test(relativePath));
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

        // Check if it's auto-generated
        if (basename.includes('grammar') && ext === '.py') {
            return 'auto-generated';
        }

        // Check for core components
        if (basename.includes('parser') || basename.includes('main') || basename.includes('core')) {
            return 'core-component';
        }

        // Check for test files
        if (relativePath.includes('test') || basename.includes('test') || basename.includes('spec')) {
            return 'test';
        }

        // Check for documentation
        if (ext === '.md' || basename.includes('readme') || basename.includes('doc')) {
            return 'documentation';
        }

        // Check for configuration
        if (basename.includes('config') || ext === '.json' || ext === '.yml' || ext === '.yaml' || ext === '.toml') {
            return 'configuration';
        }

        // Check for build/deployment
        if (basename.includes('build') || basename.includes('deploy') || basename.includes('docker') || basename.includes('makefile')) {
            return 'build-deployment';
        }

        // Default to source code
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
            try {
                const items = fs.readdirSync(currentPath);
                
                for (const item of items) {
                    const itemPath = path.join(currentPath, item);
                    
                    if (this.shouldExclude(itemPath)) {
                        continue;
                    }

                    const stat = fs.statSync(itemPath);
                    
                    if (stat.isDirectory()) {
                        scanRecursive(itemPath);
                    } else if (stat.isFile()) {
                        results.totalFiles++;
                        
                        const lineCount = this.countLines(itemPath);
                        const category = this.categorizeFile(itemPath);
                        const relativePath = path.relative(this.rootPath, itemPath);
                        
                        results.summary.totalLines += lineCount;
                        
                        // Initialize category if not exists
                        if (!results.filesByCategory[category]) {
                            results.filesByCategory[category] = [];
                            results.summary.categories[category] = { count: 0, totalLines: 0 };
                        }
                        
                        results.filesByCategory[category].push({
                            path: relativePath,
                            lines: lineCount,
                            size: stat.size
                        });
                        
                        results.summary.categories[category].count++;
                        results.summary.categories[category].totalLines += lineCount;
                        
                        // Check if it's a large file
                        if (lineCount > this.largeFileThreshold) {
                            results.largeFiles.push({
                                path: relativePath,
                                lines: lineCount,
                                category: category,
                                size: stat.size
                            });
                            results.summary.largeFileCount++;
                        }
                    }
                }
            } catch (error) {
                console.warn(`Warning: Could not scan directory ${currentPath}: ${error.message}`);
            }
        };

        scanRecursive(dirPath);
        
        // Sort large files by line count (descending)
        results.largeFiles.sort((a, b) => b.lines - a.lines);
        
        return results;
    }

    generateReport(analysisResults) {
        const report = {
            timestamp: new Date().toISOString(),
            summary: analysisResults.summary,
            largeFiles: analysisResults.largeFiles,
            recommendations: this.generateRecommendations(analysisResults)
        };

        return report;
    }

    generateRecommendations(results) {
        const recommendations = [];

        // Check for very large files
        const veryLargeFiles = results.largeFiles.filter(f => f.lines > 2000);
        if (veryLargeFiles.length > 0) {
            recommendations.push({
                type: 'code-organization',
                priority: 'medium',
                message: `Consider refactoring ${veryLargeFiles.length} very large files (>2000 lines) for better maintainability`,
                files: veryLargeFiles.map(f => f.path)
            });
        }

        // Check for too many large files in source code category
        const largeSourceFiles = results.largeFiles.filter(f => f.category === 'source-code');
        if (largeSourceFiles.length > 5) {
            recommendations.push({
                type: 'architecture',
                priority: 'low',
                message: `Consider modularizing ${largeSourceFiles.length} large source code files`,
                files: largeSourceFiles.map(f => f.path)
            });
        }

        // Check for auto-generated files that are very large
        const largeAutoGenerated = results.largeFiles.filter(f => f.category === 'auto-generated');
        if (largeAutoGenerated.length > 0) {
            recommendations.push({
                type: 'build-optimization',
                priority: 'low',
                message: `${largeAutoGenerated.length} large auto-generated files detected - consider build optimization`,
                files: largeAutoGenerated.map(f => f.path)
            });
        }

        return recommendations;
    }

    formatForCICD(analysisResults) {
        const report = this.generateReport(analysisResults);
        
        let output = "## Code Cleanliness Analysis\n\n";
        
        if (report.largeFiles.length > 0) {
            output += "### Large Files (>500 lines):\n";
            report.largeFiles.forEach(file => {
                output += `${file.lines} lines: ./${file.path}\n`;
            });
            output += "\n";
        } else {
            output += "### Large Files (>500 lines):\n";
            output += "✅ No files exceed 500 lines threshold\n\n";
        }

        // Add category breakdown
        output += "### File Category Breakdown:\n";
        Object.entries(report.summary.categories).forEach(([category, stats]) => {
            output += `**${category.replace('-', ' ').toUpperCase()}**: ${stats.count} files, ${stats.totalLines} total lines\n`;
        });
        output += "\n";

        // Add recommendations if any
        if (report.recommendations.length > 0) {
            output += "### Recommendations:\n";
            report.recommendations.forEach(rec => {
                const priority = rec.priority.toUpperCase();
                output += `- **${priority}**: ${rec.message}\n`;
            });
            output += "\n";
        }

        return output;
    }
}

// CLI usage
if (import.meta.url === `file://${process.argv[1]}`) {
    const analyzer = new FileAnalyzer();
    
    console.log('🔍 Analyzing repository files...');
    
    try {
        const results = await analyzer.scanDirectory();
        const report = analyzer.generateReport(results);
        
        if (process.argv.includes('--json')) {
            console.log(JSON.stringify(report, null, 2));
        } else if (process.argv.includes('--cicd')) {
            console.log(analyzer.formatForCICD(results));
        } else {
            console.log('\n📊 File Analysis Summary:');
            console.log(`Total files scanned: ${results.totalFiles}`);
            console.log(`Total lines of code: ${report.summary.totalLines.toLocaleString()}`);
            console.log(`Large files (>500 lines): ${report.summary.largeFileCount}`);
            
            if (report.largeFiles.length > 0) {
                console.log('\n📋 Large Files:');
                report.largeFiles.slice(0, 10).forEach(file => {
                    console.log(`  ${file.lines.toString().padStart(4)} lines: ${file.path} (${file.category})`);
                });
                
                if (report.largeFiles.length > 10) {
                    console.log(`  ... and ${report.largeFiles.length - 10} more`);
                }
            }
            
            if (report.recommendations.length > 0) {
                console.log('\n💡 Recommendations:');
                report.recommendations.forEach(rec => {
                    console.log(`  ${rec.priority.toUpperCase()}: ${rec.message}`);
                });
            }
        }
    } catch (error) {
        console.error('❌ Error during file analysis:', error.message);
        process.exit(1);
    }
}

export default FileAnalyzer;