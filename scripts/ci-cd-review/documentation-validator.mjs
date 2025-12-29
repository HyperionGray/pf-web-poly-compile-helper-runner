#!/usr/bin/env node

/**
 * Documentation Validator for CI/CD Review
 * Validates documentation completeness and quality
 */

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

class DocumentationValidator {
    constructor(rootPath = path.resolve(__dirname, '../..')) {
        this.rootPath = rootPath;
        this.requiredRootDocs = [
            'README.md',
            'QUICKSTART.md',
            'LICENSE.md',
            'LICENSE'
        ];
        this.requiredDocsStructure = {
            'docs/CHANGELOG.md': 'changelog',
            'docs/development/CONTRIBUTING.md': 'contributing guidelines',
            'docs/development/CODE_OF_CONDUCT.md': 'code of conduct',
            'docs/security/SECURITY.md': 'security policy',
            'docs/installation/INSTALL.md': 'installation guide'
        };
        this.requiredReadmeSections = [
            'Installation',
            'Usage',
            'Features',
            'Contributing',
            'License',
            'Documentation',
            'Examples',
            'API'
        ];
    }

    async validateDocumentationStructure() {
        const results = {
            rootDocumentation: {},
            docsDirectory: {},
            readmeAnalysis: {},
            summary: {
                totalRequired: 0,
                totalFound: 0,
                missingFiles: [],
                extraFiles: []
            }
        };

        // Check root documentation files
        console.log('📋 Checking root documentation files...');
        for (const docFile of this.requiredRootDocs) {
            const filePath = path.join(this.rootPath, docFile);
            const exists = fs.existsSync(filePath);
            
            results.rootDocumentation[docFile] = {
                exists,
                path: filePath,
                wordCount: 0,
                status: exists ? '✅' : '❌'
            };

            results.summary.totalRequired++;
            
            if (exists) {
                results.summary.totalFound++;
                try {
                    const content = fs.readFileSync(filePath, 'utf8');
                    results.rootDocumentation[docFile].wordCount = this.countWords(content);
                } catch (error) {
                    console.warn(`Warning: Could not read ${docFile}: ${error.message}`);
                }
            } else {
                results.summary.missingFiles.push(docFile);
            }
        }

        // Check docs directory structure
        console.log('📁 Checking docs directory structure...');
        for (const [docPath, description] of Object.entries(this.requiredDocsStructure)) {
            const fullPath = path.join(this.rootPath, docPath);
            const exists = fs.existsSync(fullPath);
            
            results.docsDirectory[docPath] = {
                exists,
                description,
                path: fullPath,
                wordCount: 0,
                status: exists ? '✅' : '❌'
            };

            results.summary.totalRequired++;
            
            if (exists) {
                results.summary.totalFound++;
                try {
                    const content = fs.readFileSync(fullPath, 'utf8');
                    results.docsDirectory[docPath].wordCount = this.countWords(content);
                } catch (error) {
                    console.warn(`Warning: Could not read ${docPath}: ${error.message}`);
                }
            } else {
                results.summary.missingFiles.push(docPath);
            }
        }

        // Analyze README.md content
        console.log('📖 Analyzing README.md content...');
        const readmePath = path.join(this.rootPath, 'README.md');
        if (fs.existsSync(readmePath)) {
            results.readmeAnalysis = await this.analyzeReadmeContent(readmePath);
        } else {
            results.readmeAnalysis = {
                sections: {},
                missingsections: this.requiredReadmeSections,
                totalSections: 0,
                requiredSections: this.requiredReadmeSections.length
            };
        }

        return results;
    }

    async analyzeReadmeContent(readmePath) {
        const content = fs.readFileSync(readmePath, 'utf8');
        const lines = content.split('\n');
        
        const analysis = {
            sections: {},
            missingsections: [],
            totalSections: 0,
            requiredSections: this.requiredReadmeSections.length,
            wordCount: this.countWords(content)
        };

        // Find all sections (headers)
        const sectionRegex = /^#+\s+(.+)$/;
        const foundSections = new Set();
        
        for (const line of lines) {
            const match = line.match(sectionRegex);
            if (match) {
                const sectionTitle = match[1].trim();
                foundSections.add(sectionTitle);
                analysis.totalSections++;
            }
        }

        // Check for required sections
        for (const requiredSection of this.requiredReadmeSections) {
            const found = Array.from(foundSections).some(section => 
                section.toLowerCase().includes(requiredSection.toLowerCase())
            );
            
            analysis.sections[requiredSection] = {
                found,
                status: found ? '✅' : '❌'
            };
            
            if (!found) {
                analysis.missingsections.push(requiredSection);
            }
        }

        return analysis;
    }

    countWords(text) {
        // Remove markdown syntax and count words
        const cleanText = text
            .replace(/```[\s\S]*?```/g, '') // Remove code blocks
            .replace(/`[^`]*`/g, '') // Remove inline code
            .replace(/\[([^\]]*)\]\([^)]*\)/g, '$1') // Remove links, keep text
            .replace(/[#*_~`]/g, '') // Remove markdown formatting
            .replace(/\s+/g, ' ') // Normalize whitespace
            .trim();
        
        return cleanText ? cleanText.split(' ').length : 0;
    }

    async scanAdditionalDocs() {
        const docsPath = path.join(this.rootPath, 'docs');
        const additionalDocs = [];
        
        if (!fs.existsSync(docsPath)) {
            return additionalDocs;
        }

        const scanRecursive = (dirPath, relativePath = '') => {
            try {
                const items = fs.readdirSync(dirPath);
                
                for (const item of items) {
                    const itemPath = path.join(dirPath, item);
                    const itemRelativePath = path.join(relativePath, item);
                    const stat = fs.statSync(itemPath);
                    
                    if (stat.isDirectory()) {
                        scanRecursive(itemPath, itemRelativePath);
                    } else if (stat.isFile() && item.endsWith('.md')) {
                        const fullRelativePath = path.join('docs', itemRelativePath);
                        
                        // Skip if it's already in required docs
                        if (!this.requiredDocsStructure[fullRelativePath]) {
                            try {
                                const content = fs.readFileSync(itemPath, 'utf8');
                                additionalDocs.push({
                                    path: fullRelativePath,
                                    wordCount: this.countWords(content),
                                    size: stat.size
                                });
                            } catch (error) {
                                console.warn(`Warning: Could not read ${fullRelativePath}: ${error.message}`);
                            }
                        }
                    }
                }
            } catch (error) {
                console.warn(`Warning: Could not scan directory ${dirPath}: ${error.message}`);
            }
        };

        scanRecursive(docsPath);
        return additionalDocs;
    }

    generateReport(validationResults, additionalDocs = []) {
        const report = {
            timestamp: new Date().toISOString(),
            summary: {
                ...validationResults.summary,
                completionPercentage: Math.round((validationResults.summary.totalFound / validationResults.summary.totalRequired) * 100),
                readmeCompleteness: Math.round(((validationResults.readmeAnalysis.requiredSections - validationResults.readmeAnalysis.missingSections.length) / validationResults.readmeAnalysis.requiredSections) * 100)
            },
            rootDocumentation: validationResults.rootDocumentation,
            docsDirectory: validationResults.docsDirectory,
            readmeAnalysis: validationResults.readmeAnalysis,
            additionalDocs: additionalDocs,
            recommendations: this.generateRecommendations(validationResults, additionalDocs)
        };

        return report;
    }

    generateRecommendations(results, additionalDocs) {
        const recommendations = [];

        // Check for missing required files
        if (results.summary.missingFiles.length > 0) {
            recommendations.push({
                type: 'missing-documentation',
                priority: 'high',
                message: `Missing ${results.summary.missingFiles.length} required documentation files`,
                files: results.summary.missingFiles
            });
        }

        // Check for missing README sections
        if (results.readmeAnalysis.missingSection && results.readmeAnalysis.missingSection.length > 0) {
            recommendations.push({
                type: 'readme-completeness',
                priority: 'medium',
                message: `README.md missing ${results.readmeAnalysis.missingSection.length} required sections`,
                sections: results.readmeAnalysis.missingSection
            });
        }

        // Check for very short documentation files
        const shortDocs = [];
        Object.entries(results.rootDocumentation).forEach(([file, info]) => {
            if (info.exists && info.wordCount < 50 && file !== 'LICENSE') {
                shortDocs.push(file);
            }
        });

        if (shortDocs.length > 0) {
            recommendations.push({
                type: 'documentation-quality',
                priority: 'low',
                message: `${shortDocs.length} documentation files are very short (<50 words)`,
                files: shortDocs
            });
        }

        return recommendations;
    }

    formatForCICD(validationResults, additionalDocs = []) {
        const report = this.generateReport(validationResults, additionalDocs);
        
        let output = "## Documentation Analysis\n\n";
        
        // Essential Documentation Files
        output += "### Essential Documentation Files:\n";
        output += "#### Root Documentation:\n";
        
        Object.entries(report.rootDocumentation).forEach(([file, info]) => {
            output += `${info.status} ${file}`;
            if (info.exists && info.wordCount > 0) {
                output += ` (${info.wordCount} words)`;
            }
            output += "\n";
        });
        
        output += "\n#### Documentation in docs/:\n";
        Object.entries(report.docsDirectory).forEach(([file, info]) => {
            output += `${info.status} ${file}`;
            if (info.exists && info.wordCount > 0) {
                output += ` (${info.wordCount} words)`;
            }
            output += "\n";
        });

        // README.md Content Check
        output += "\n### README.md Content Check:\n";
        Object.entries(report.readmeAnalysis.sections || {}).forEach(([section, info]) => {
            output += `${info.status} Contains '${section}' section\n`;
        });

        // Summary statistics
        output += `\n### Documentation Summary:\n`;
        output += `- **Completion Rate**: ${report.summary.completionPercentage}% (${report.summary.totalFound}/${report.summary.totalRequired} required files)\n`;
        output += `- **README Completeness**: ${report.summary.readmeCompleteness}% (${report.readmeAnalysis.requiredSections - (report.readmeAnalysis.missingSection?.length || 0)}/${report.readmeAnalysis.requiredSections} required sections)\n`;
        
        if (additionalDocs.length > 0) {
            output += `- **Additional Documentation**: ${additionalDocs.length} extra documentation files found\n`;
        }

        // Add recommendations if any
        if (report.recommendations.length > 0) {
            output += "\n### Documentation Recommendations:\n";
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
    const validator = new DocumentationValidator();
    
    console.log('📚 Validating documentation structure...');
    
    try {
        const results = await validator.validateDocumentationStructure();
        const additionalDocs = await validator.scanAdditionalDocs();
        const report = validator.generateReport(results, additionalDocs);
        
        if (process.argv.includes('--json')) {
            console.log(JSON.stringify(report, null, 2));
        } else if (process.argv.includes('--cicd')) {
            console.log(validator.formatForCICD(results, additionalDocs));
        } else {
            console.log('\n📊 Documentation Validation Summary:');
            console.log(`Required files found: ${report.summary.totalFound}/${report.summary.totalRequired} (${report.summary.completionPercentage}%)`);
            console.log(`README completeness: ${report.summary.readmeCompleteness}%`);
            console.log(`Additional docs found: ${additionalDocs.length}`);
            
            if (report.summary.missingFiles.length > 0) {
                console.log('\n❌ Missing Required Files:');
                report.summary.missingFiles.forEach(file => {
                    console.log(`  - ${file}`);
                });
            }
            
            if (results.readmeAnalysis.missingSection && results.readmeAnalysis.missingSection.length > 0) {
                console.log('\n📖 Missing README Sections:');
                results.readmeAnalysis.missingSection.forEach(section => {
                    console.log(`  - ${section}`);
                });
            }
            
            if (report.recommendations.length > 0) {
                console.log('\n💡 Recommendations:');
                report.recommendations.forEach(rec => {
                    console.log(`  ${rec.priority.toUpperCase()}: ${rec.message}`);
                });
            }
        }
    } catch (error) {
        console.error('❌ Error during documentation validation:', error.message);
        process.exit(1);
    }
}

export default DocumentationValidator;