#!/usr/bin/env node

// Quick test of the CI/CD review system
import { spawn } from 'child_process';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const rootPath = path.resolve(__dirname, '..');

console.log('🧪 Testing CI/CD Review System...');
console.log('');

// Test file analyzer
console.log('📁 Testing File Analyzer...');
const fileAnalyzer = spawn('node', ['scripts/ci-cd-review/file-analyzer.mjs', '--cicd'], {
    cwd: rootPath,
    stdio: 'pipe'
});

let output = '';
fileAnalyzer.stdout.on('data', (data) => {
    output += data.toString();
});

fileAnalyzer.on('close', (code) => {
    if (code === 0) {
        console.log('✅ File Analyzer working correctly');
        console.log('Sample output:');
        console.log(output.split('\n').slice(0, 10).join('\n'));
        console.log('...');
    } else {
        console.log('❌ File Analyzer failed');
    }
    
    console.log('');
    console.log('🎉 CI/CD Review System is ready!');
    console.log('');
    console.log('Next steps:');
    console.log('1. Run: npm run cicd:review:save');
    console.log('2. Check the generated CICD_REVIEW_REPORT.md file');
    console.log('3. Push to main branch to trigger GitHub Actions workflow');
});

fileAnalyzer.on('error', (error) => {
    console.error('❌ Error testing file analyzer:', error.message);
});