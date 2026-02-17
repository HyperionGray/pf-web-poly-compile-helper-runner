#!/usr/bin/env node

/**
 * Intelligent Workflow Engine for Security Tool Orchestration
 * Coordinates multiple security tools to create smart, automated workflows
 */

import { execSync, spawn } from 'child_process';
import { existsSync, readFileSync, writeFileSync, mkdirSync } from 'fs';
import { join, dirname, basename, extname } from 'path';
import { fileURLToPath } from 'url';
import { ToolDetector } from './tool-detector.mjs';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

class WorkflowEngine {
    constructor() {
        this.detector = new ToolDetector();
        this.workflows = new Map();
        this.results = new Map();
        this.initializeWorkflows();
    }

    async initialize() {
        console.log('🚀 Initializing Workflow Engine...');
        await this.detector.detectAllTools();
        console.log('✅ Tool detection complete');
    }

    initializeWorkflows() {
        // Define intelligent workflows
        this.workflowDefinitions = {
            'binary-analysis': {
                description: 'Complete binary analysis workflow',
                steps: [
                    { name: 'file-identification', tools: ['file'], required: true },
                    { name: 'security-features', tools: ['checksec'], required: false },
                    { name: 'strings-extraction', tools: ['strings'], required: false },
                    { name: 'elf-analysis', tools: ['readelf'], required: false },
                    { name: 'disassembly', tools: ['objdump', 'radare2'], required: false },
                    { name: 'debugging-prep', tools: ['gdb', 'lldb'], required: false }
                ]
            },
            'binary-exploit': {
                description: 'Binary exploitation workflow',
                steps: [
                    { name: 'binary-analysis', workflow: 'binary-analysis' },
                    { name: 'vulnerability-scan', tools: ['checksec'], required: true },
                    { name: 'rop-analysis', tools: ['ROPgadget', 'ropper'], required: false },
                    { name: 'exploit-generation', tools: ['pwntools'], required: false }
                ]
            },
            'web-security': {
                description: 'Web application security assessment',
                steps: [
                    { name: 'service-discovery', tools: ['nmap'], required: false },
                    { name: 'web-scanning', custom: 'web-scanner' },
                    { name: 'vulnerability-testing', custom: 'web-fuzzer' }
                ]
            },
            'reverse-engineering': {
                description: 'Complete reverse engineering workflow',
                steps: [
                    { name: 'binary-analysis', workflow: 'binary-analysis' },
                    { name: 'decompilation', tools: ['retdec-decompiler'], required: false },
                    { name: 'advanced-analysis', tools: ['radare2'], required: false }
                ]
            }
        };
    }

    async executeWorkflow(workflowName, target, options = {}) {
        const workflowId = `${workflowName}-${Date.now()}`;
        console.log(`🔄 Starting workflow: ${workflowName} (ID: ${workflowId})`);
        
        const workflow = this.workflowDefinitions[workflowName];
        if (!workflow) {
            throw new Error(`Unknown workflow: ${workflowName}`);
        }

        const results = {
            workflowId,
            workflowName,
            target,
            startTime: new Date().toISOString(),
            steps: [],
            summary: {},
            success: false
        };

        try {
            for (const step of workflow.steps) {
                console.log(`  📋 Executing step: ${step.name}`);
                const stepResult = await this.executeStep(step, target, options);
                results.steps.push(stepResult);
                
                if (step.required && !stepResult.success) {
                    throw new Error(`Required step failed: ${step.name}`);
                }
            }

            results.success = true;
            results.endTime = new Date().toISOString();
            results.summary = this.generateSummary(results);
            
        } catch (error) {
            results.error = error.message;
            results.endTime = new Date().toISOString();
            console.error(`❌ Workflow failed: ${error.message}`);
        }

        this.results.set(workflowId, results);
        
        if (options.output) {
            this.saveResults(results, options.output);
        }

        return results;
    }

    async executeStep(step, target, options) {
        const stepResult = {
            name: step.name,
            startTime: new Date().toISOString(),
            success: false,
            output: null,
            toolUsed: null
        };

        try {
            if (step.workflow) {
                // Execute sub-workflow
                const subResult = await this.executeWorkflow(step.workflow, target, { ...options, output: null });
                stepResult.success = subResult.success;
                stepResult.output = subResult;
                stepResult.toolUsed = 'sub-workflow';
            } else if (step.custom) {
                // Execute custom function
                stepResult.output = await this.executeCustomStep(step.custom, target, options);
                stepResult.success = true;
                stepResult.toolUsed = step.custom;
            } else if (step.tools) {
                // Execute tool-based step
                const availableTools = step.tools.filter(tool => 
                    this.detector.tools.get(tool)?.available
                );
                
                if (availableTools.length === 0) {
                    stepResult.error = `No available tools for step: ${step.name}`;
                    return stepResult;
                }

                // Use the first available tool
                const toolName = availableTools[0];
                stepResult.output = await this.executeTool(toolName, target, options);
                stepResult.success = true;
                stepResult.toolUsed = toolName;
            }
        } catch (error) {
            stepResult.error = error.message;
        }

        stepResult.endTime = new Date().toISOString();
        return stepResult;
    }

    async executeTool(toolName, target, options) {
        const tool = this.detector.tools.get(toolName);
        if (!tool || !tool.available) {
            throw new Error(`Tool not available: ${toolName}`);
        }

        console.log(`    🔧 Using tool: ${toolName}`);

        // Tool-specific execution logic
        switch (toolName) {
            case 'file':
                return this.executeCommand(`file "${target}"`);
            
            case 'checksec':
                return this.executeCommand(`checksec --file="${target}"`);
            
            case 'strings':
                return this.executeCommand(`strings "${target}" | head -100`);
            
            case 'readelf':
                return this.executeCommand(`readelf -a "${target}"`);
            
            case 'objdump':
                return this.executeCommand(`objdump -d "${target}" | head -200`);
            
            case 'ROPgadget':
                return this.executeCommand(`ROPgadget --binary "${target}" --only "pop|ret" | head -50`);
            
            case 'radare2':
                return this.executeCommand(`r2 -q -c "aaa; pdf @ main" "${target}"`);
            
            default:
                return this.executeCommand(`${tool.command} "${target}"`);
        }
    }

    async executeCustomStep(stepName, target, options) {
        console.log(`    🎯 Executing custom step: ${stepName}`);
        
        switch (stepName) {
            case 'web-scanner':
                return this.executeWebScanner(target, options);
            
            case 'web-fuzzer':
                return this.executeWebFuzzer(target, options);
            
            default:
                throw new Error(`Unknown custom step: ${stepName}`);
        }
    }

    async executeWebScanner(target, options) {
        // Use the existing security scanner
        const scannerPath = join(__dirname, '..', 'security', 'scanner.mjs');
        if (existsSync(scannerPath)) {
            return this.executeCommand(`node "${scannerPath}" "${target}" --json`);
        } else {
            return { message: 'Web scanner not available', target };
        }
    }

    async executeWebFuzzer(target, options) {
        // Use the existing security fuzzer
        const fuzzerPath = join(__dirname, '..', 'security', 'fuzzer.mjs');
        if (existsSync(fuzzerPath)) {
            return this.executeCommand(`node "${fuzzerPath}" "${target}" --type all --json`);
        } else {
            return { message: 'Web fuzzer not available', target };
        }
    }

    executeCommand(command) {
        try {
            const output = execSync(command, {
                timeout: 30000,
                encoding: 'utf8',
                maxBuffer: 1024 * 1024 // 1MB
            });
            return { command, output, success: true };
        } catch (error) {
            return { command, error: error.message, success: false };
        }
    }

    generateSummary(results) {
        const summary = {
            totalSteps: results.steps.length,
            successfulSteps: results.steps.filter(s => s.success).length,
            failedSteps: results.steps.filter(s => !s.success).length,
            toolsUsed: [...new Set(results.steps.map(s => s.toolUsed).filter(Boolean))],
            duration: results.endTime ? 
                new Date(results.endTime) - new Date(results.startTime) : null
        };

        // Add workflow-specific insights
        if (results.workflowName === 'binary-analysis') {
            summary.insights = this.generateBinaryAnalysisInsights(results);
        } else if (results.workflowName === 'web-security') {
            summary.insights = this.generateWebSecurityInsights(results);
        }

        return summary;
    }

    generateBinaryAnalysisInsights(results) {
        const insights = [];
        
        // Check for security features
        const checksecStep = results.steps.find(s => s.toolUsed === 'checksec');
        if (checksecStep && checksecStep.output) {
            const output = checksecStep.output.output || '';
            if (output.includes('No canary found')) {
                insights.push('⚠️  Stack canary protection disabled - vulnerable to buffer overflows');
            }
            if (output.includes('NX disabled')) {
                insights.push('⚠️  NX bit disabled - shellcode execution possible');
            }
            if (output.includes('No PIE')) {
                insights.push('⚠️  Position Independent Executable disabled - predictable memory layout');
            }
        }

        // Check file type
        const fileStep = results.steps.find(s => s.toolUsed === 'file');
        if (fileStep && fileStep.output) {
            const output = fileStep.output.output || '';
            if (output.includes('not stripped')) {
                insights.push('ℹ️  Binary contains debug symbols - easier to analyze');
            }
            if (output.includes('statically linked')) {
                insights.push('ℹ️  Statically linked binary - all dependencies included');
            }
        }

        return insights;
    }

    generateWebSecurityInsights(results) {
        const insights = [];
        
        // Analyze web scanning results
        const scanStep = results.steps.find(s => s.name === 'web-scanning');
        if (scanStep && scanStep.output) {
            // Add web-specific insights based on scan results
            insights.push('🌐 Web application analysis completed');
        }

        return insights;
    }

    saveResults(results, outputPath) {
        try {
            const dir = dirname(outputPath);
            if (!existsSync(dir)) {
                mkdirSync(dir, { recursive: true });
            }
            
            writeFileSync(outputPath, JSON.stringify(results, null, 2));
            console.log(`📄 Results saved to: ${outputPath}`);
        } catch (error) {
            console.error(`Failed to save results: ${error.message}`);
        }
    }

    getWorkflowStatus() {
        return Array.from(this.results.values()).map(result => ({
            id: result.workflowId,
            name: result.workflowName,
            target: result.target,
            status: result.success ? 'completed' : 'failed',
            startTime: result.startTime,
            endTime: result.endTime
        }));
    }
}

// CLI Interface
async function main() {
    const args = process.argv.slice(2);
    
    if (args.length === 0) {
        console.log(`
🤖 Intelligent Security Workflow Engine

Usage:
  workflow-engine.mjs <workflow> --target <target> [options]

Workflows:
  binary-analysis     Complete binary analysis
  binary-exploit      Binary exploitation workflow  
  web-security        Web application security assessment
  reverse-engineering Complete reverse engineering workflow

Options:
  --target <path>     Target file or URL
  --output <path>     Output file for results
  --verbose           Verbose output
  --generate-payloads Generate exploit payloads
  --comprehensive     Run comprehensive analysis

Examples:
  workflow-engine.mjs binary-analysis --target ./binary --output analysis.json
  workflow-engine.mjs web-security --target http://localhost:8080 --comprehensive
        `);
        process.exit(1);
    }

    const workflowName = args[0];
    const target = args[args.indexOf('--target') + 1];
    const output = args.includes('--output') ? args[args.indexOf('--output') + 1] : null;
    const verbose = args.includes('--verbose');
    
    const options = {
        output,
        verbose,
        generatePayloads: args.includes('--generate-payloads'),
        comprehensive: args.includes('--comprehensive'),
        deepAnalysis: args.includes('--deep-analysis')
    };

    if (!target) {
        console.error('❌ Target is required. Use --target <path_or_url>');
        process.exit(1);
    }

    const engine = new WorkflowEngine();
    await engine.initialize();

    try {
        const results = await engine.executeWorkflow(workflowName, target, options);
        
        if (results.success) {
            console.log('✅ Workflow completed successfully!');
            if (results.summary.insights) {
                console.log('\n🔍 Key Insights:');
                results.summary.insights.forEach(insight => console.log(`  ${insight}`));
            }
        } else {
            console.log('❌ Workflow failed');
            process.exit(1);
        }
    } catch (error) {
        console.error(`❌ Error: ${error.message}`);
        process.exit(1);
    }
}

if (import.meta.url === `file://${process.argv[1]}`) {
    main().catch(console.error);
}

export { WorkflowEngine };