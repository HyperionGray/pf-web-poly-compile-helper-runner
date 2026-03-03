#!/usr/bin/env node
/**
 * Test suite for code-analyzer tool
 * Validates that the code analyzer works correctly
 */

import { spawn } from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import CodeAnalyzer from '../tools/analysis/code-analyzer.mjs';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Test utilities
function assert(condition, message) {
  if (!condition) {
    throw new Error(`Assertion failed: ${message}`);
  }
}

function log(message) {
  console.log(`  ${message}`);
}

// Test: Basic analyzer instantiation
async function testAnalyzerInstantiation() {
  console.log('\n🧪 Test: Analyzer Instantiation');
  
  const analyzer = new CodeAnalyzer({
    rootDir: process.cwd(),
    verbose: false
  });
  
  assert(analyzer.rootDir, 'Analyzer should have rootDir');
  assert(analyzer.results, 'Analyzer should have results object');
  assert(analyzer.results.security, 'Results should have security array');
  assert(analyzer.results.performance, 'Results should have performance array');
  assert(analyzer.results.architecture, 'Results should have architecture array');
  
  log('✓ Analyzer instantiates correctly');
}

// Test: Statistics collection
async function testStatisticsCollection() {
  console.log('\n🧪 Test: Statistics Collection');
  
  const analyzer = new CodeAnalyzer({
    rootDir: process.cwd(),
    verbose: false
  });
  
  const stats = await analyzer.collectStatistics();
  
  assert(stats, 'Should return statistics object');
  assert(typeof stats.python === 'number', 'Should count Python files');
  assert(typeof stats.javascript === 'number', 'Should count JavaScript files');
  assert(typeof stats.typescript === 'number', 'Should count TypeScript files');
  assert(stats.python > 0 || stats.javascript > 0, 'Should find at least some files');
  
  log('✓ Statistics collection works');
  log(`  Python files: ${stats.python}`);
  log(`  JavaScript files: ${stats.javascript}`);
  log(`  TypeScript files: ${stats.typescript}`);
}

// Test: Security analysis
async function testSecurityAnalysis() {
  console.log('\n🧪 Test: Security Analysis');
  
  const analyzer = new CodeAnalyzer({
    rootDir: process.cwd(),
    verbose: false
  });
  
  const findings = await analyzer.analyzeSecurityVulnerabilities();
  
  assert(Array.isArray(findings), 'Should return array of findings');
  
  // If any findings exist, validate their structure
  if (findings.length > 0) {
    const finding = findings[0];
    assert(finding.category, 'Finding should have category');
    assert(finding.severity, 'Finding should have severity');
    assert(finding.title, 'Finding should have title');
    assert(finding.description, 'Finding should have description');
    assert(finding.recommendation, 'Finding should have recommendation');
  }
  
  log('✓ Security analysis completed');
  log(`  Found ${findings.length} security findings`);
}

// Test: Performance analysis
async function testPerformanceAnalysis() {
  console.log('\n🧪 Test: Performance Analysis');
  
  const analyzer = new CodeAnalyzer({
    rootDir: process.cwd(),
    verbose: false
  });
  
  const findings = await analyzer.analyzePerformance();
  
  assert(Array.isArray(findings), 'Should return array of findings');
  
  log('✓ Performance analysis completed');
  log(`  Found ${findings.length} performance optimization opportunities`);
}

// Test: Architecture analysis
async function testArchitectureAnalysis() {
  console.log('\n🧪 Test: Architecture Analysis');
  
  const analyzer = new CodeAnalyzer({
    rootDir: process.cwd(),
    verbose: false
  });
  
  const findings = await analyzer.analyzeArchitecture();
  
  assert(Array.isArray(findings), 'Should return array of findings');
  
  log('✓ Architecture analysis completed');
  log(`  Found ${findings.length} architecture recommendations`);
}

// Test: Test coverage analysis
async function testCoverageAnalysis() {
  console.log('\n🧪 Test: Test Coverage Analysis');
  
  const analyzer = new CodeAnalyzer({
    rootDir: process.cwd(),
    verbose: false
  });
  
  const findings = await analyzer.analyzeTestCoverage();
  
  assert(Array.isArray(findings), 'Should return array of findings');
  
  log('✓ Test coverage analysis completed');
  log(`  Found ${findings.length} testing recommendations`);
}

// Test: Documentation analysis
async function testDocumentationAnalysis() {
  console.log('\n🧪 Test: Documentation Analysis');
  
  const analyzer = new CodeAnalyzer({
    rootDir: process.cwd(),
    verbose: false
  });
  
  const findings = await analyzer.analyzeDocumentation();
  
  assert(Array.isArray(findings), 'Should return array of findings');
  
  log('✓ Documentation analysis completed');
  log(`  Found ${findings.length} documentation recommendations`);
}

// Test: Full analysis run
async function testFullAnalysis() {
  console.log('\n🧪 Test: Full Analysis Run');
  
  const analyzer = new CodeAnalyzer({
    rootDir: process.cwd(),
    verbose: false
  });
  
  const results = await analyzer.runAnalysis();
  
  assert(results, 'Should return results object');
  assert(results.statistics, 'Should have statistics');
  assert(results.security, 'Should have security findings');
  assert(results.performance, 'Should have performance findings');
  assert(results.architecture, 'Should have architecture findings');
  assert(results.testing, 'Should have testing findings');
  assert(results.documentation, 'Should have documentation findings');
  
  log('✓ Full analysis completed successfully');
}

// Test: Report generation
async function testReportGeneration() {
  console.log('\n🧪 Test: Report Generation');
  
  const analyzer = new CodeAnalyzer({
    rootDir: process.cwd(),
    verbose: false
  });
  
  await analyzer.runAnalysis();
  const report = analyzer.generateReport();
  
  assert(typeof report === 'string', 'Should generate string report');
  assert(report.includes('# GPT-5 Advanced Code Analysis Report'), 'Should have proper header');
  assert(report.includes('## Repository Statistics'), 'Should include statistics');
  assert(report.includes('## 🔒 Security Analysis'), 'Should include security section');
  assert(report.includes('## ⚡ Performance Optimization'), 'Should include performance section');
  assert(report.includes('## 🏗️ Architecture Quality'), 'Should include architecture section');
  assert(report.includes('## 🧪 Test Coverage'), 'Should include testing section');
  assert(report.includes('## 📚 Documentation Quality'), 'Should include documentation section');
  assert(report.includes('## ✅ Action Items'), 'Should include action items');
  
  log('✓ Report generation works correctly');
  log(`  Report length: ${report.length} characters`);
}

// Test: CLI execution
async function testCLI() {
  console.log('\n🧪 Test: CLI Execution');
  
  const tmpFile = '/tmp/test-analyzer-output.md';
  
  return new Promise((resolve, reject) => {
    const proc = spawn('node', [
      'tools/analysis/code-analyzer.mjs',
      '.',
      '--output',
      tmpFile
    ]);
    
    let output = '';
    proc.stdout.on('data', (data) => {
      output += data.toString();
    });
    
    let errors = '';
    proc.stderr.on('data', (data) => {
      errors += data.toString();
    });
    
    proc.on('close', (code) => {
      try {
        assert(fs.existsSync(tmpFile), 'Should create output file');
        
        const content = fs.readFileSync(tmpFile, 'utf-8');
        assert(content.length > 0, 'Output file should have content');
        assert(content.includes('# GPT-5 Advanced Code Analysis Report'), 'Should have proper header');
        
        // Clean up
        fs.unlinkSync(tmpFile);
        
        log('✓ CLI execution works correctly');
        log(`  Exit code: ${code}`);
        resolve();
      } catch (error) {
        reject(error);
      }
    });
    
    proc.on('error', reject);
    
    // Timeout after 60 seconds
    setTimeout(() => {
      proc.kill();
      reject(new Error('CLI execution timeout'));
    }, 60000);
  });
}

// Test: File finding utility
async function testFileFinding() {
  console.log('\n🧪 Test: File Finding Utility');
  
  const analyzer = new CodeAnalyzer({
    rootDir: process.cwd(),
    verbose: false
  });
  
  // Find JavaScript files
  const jsFiles = await analyzer.findFiles('*.js', ['*/node_modules/*']);
  assert(Array.isArray(jsFiles), 'Should return array of files');
  
  // Find Python files
  const pyFiles = await analyzer.findFiles('*.py', ['*/.venv/*', '*/node_modules/*']);
  assert(Array.isArray(pyFiles), 'Should return array of files');
  
  log('✓ File finding utility works');
  log(`  Found ${jsFiles.length} JS files`);
  log(`  Found ${pyFiles.length} Python files`);
}

// Main test runner
async function runTests() {
  console.log('🚀 Starting Code Analyzer Test Suite\n');
  
  try {
    await testAnalyzerInstantiation();
    await testFileFinding();
    await testStatisticsCollection();
    await testSecurityAnalysis();
    await testPerformanceAnalysis();
    await testArchitectureAnalysis();
    await testCoverageAnalysis();
    await testDocumentationAnalysis();
    await testFullAnalysis();
    await testReportGeneration();
    await testCLI();
    
    console.log('\n✅ All tests passed!\n');
  } catch (error) {
    console.error(`\n❌ Test failed: ${error.message}\n`);
    if (error.stack) {
      console.error(error.stack);
    }
    throw error;
  }
}

// Run tests if executed directly
if (import.meta.url === `file://${process.argv[1]}`) {
  runTests()
    .then(() => process.exit(0))
    .catch((error) => {
      console.error(error);
      process.exit(1);
    });
}

export { runTests };
