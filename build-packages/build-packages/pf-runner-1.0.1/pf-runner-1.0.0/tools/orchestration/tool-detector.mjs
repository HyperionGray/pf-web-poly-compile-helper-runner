#!/usr/bin/env node

/**
 * Tool Detection and Capability Discovery System
 * Scans for available security tools and maps their capabilities
 */

import { execSync, spawn } from 'child_process';
import { existsSync, readFileSync, writeFileSync } from 'fs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

class ToolDetector {
    constructor() {
        this.tools = new Map();
        this.capabilities = new Map();
        this.initializeToolDefinitions();
    }

    initializeToolDefinitions() {
        // Define all security tools and their capabilities
        this.toolDefinitions = {
            // Binary Analysis Tools
            'checksec': {
                command: 'checksec',
                testArgs: ['--version'],
                capabilities: ['binary-analysis', 'security-features'],
                category: 'binary-analysis',
                description: 'Binary security feature checker'
            },
            'gdb': {
                command: 'gdb',
                testArgs: ['--version'],
                capabilities: ['debugging', 'binary-analysis', 'exploitation'],
                category: 'debugging',
                description: 'GNU Debugger'
            },
            'lldb': {
                command: 'lldb',
                testArgs: ['--version'],
                capabilities: ['debugging', 'binary-analysis', 'exploitation'],
                category: 'debugging',
                description: 'LLVM Debugger'
            },
            'radare2': {
                command: 'r2',
                testArgs: ['-version'],
                capabilities: ['reverse-engineering', 'binary-analysis', 'disassembly'],
                category: 'reverse-engineering',
                description: 'Reverse engineering framework'
            },
            'objdump': {
                command: 'objdump',
                testArgs: ['--version'],
                capabilities: ['disassembly', 'binary-analysis'],
                category: 'binary-analysis',
                description: 'Object file dumper'
            },
            'readelf': {
                command: 'readelf',
                testArgs: ['--version'],
                capabilities: ['binary-analysis', 'elf-analysis'],
                category: 'binary-analysis',
                description: 'ELF file analyzer'
            },
            'strings': {
                command: 'strings',
                testArgs: ['--version'],
                capabilities: ['binary-analysis', 'string-extraction'],
                category: 'binary-analysis',
                description: 'String extractor'
            },
            'file': {
                command: 'file',
                testArgs: ['--version'],
                capabilities: ['file-identification', 'binary-analysis'],
                category: 'binary-analysis',
                description: 'File type identifier'
            },

            // Exploitation Tools
            'ROPgadget': {
                command: 'ROPgadget',
                testArgs: ['--version'],
                capabilities: ['rop-analysis', 'exploitation', 'gadget-finding'],
                category: 'exploitation',
                description: 'ROP gadget finder'
            },
            'ropper': {
                command: 'ropper',
                testArgs: ['--version'],
                capabilities: ['rop-analysis', 'exploitation', 'gadget-finding'],
                category: 'exploitation',
                description: 'ROP gadget finder and exploit assistant'
            },
            'pwntools': {
                command: 'python3',
                testArgs: ['-c', 'import pwn; print(pwn.__version__)'],
                capabilities: ['exploitation', 'payload-generation', 'binary-interaction'],
                category: 'exploitation',
                description: 'CTF framework and exploit development library'
            },

            // Web Security Tools
            'nmap': {
                command: 'nmap',
                testArgs: ['--version'],
                capabilities: ['network-scanning', 'service-discovery', 'web-security'],
                category: 'web-security',
                description: 'Network mapper and port scanner'
            },
            'curl': {
                command: 'curl',
                testArgs: ['--version'],
                capabilities: ['web-requests', 'api-testing', 'web-security'],
                category: 'web-security',
                description: 'HTTP client'
            },
            'wget': {
                command: 'wget',
                testArgs: ['--version'],
                capabilities: ['web-requests', 'file-download'],
                category: 'web-security',
                description: 'Web file downloader'
            },

            // Compilation and Build Tools
            'gcc': {
                command: 'gcc',
                testArgs: ['--version'],
                capabilities: ['compilation', 'payload-generation', 'binary-creation'],
                category: 'compilation',
                description: 'GNU Compiler Collection'
            },
            'clang': {
                command: 'clang',
                testArgs: ['--version'],
                capabilities: ['compilation', 'llvm-ir', 'binary-creation'],
                category: 'compilation',
                description: 'LLVM C/C++ compiler'
            },
            'rustc': {
                command: 'rustc',
                testArgs: ['--version'],
                capabilities: ['compilation', 'rust-compilation', 'wasm-compilation'],
                category: 'compilation',
                description: 'Rust compiler'
            },
            'cargo': {
                command: 'cargo',
                testArgs: ['--version'],
                capabilities: ['rust-build', 'package-management'],
                category: 'compilation',
                description: 'Rust package manager'
            },

            // Kernel and System Tools
            'strace': {
                command: 'strace',
                testArgs: ['--version'],
                capabilities: ['system-call-tracing', 'kernel-analysis', 'debugging'],
                category: 'kernel-analysis',
                description: 'System call tracer'
            },
            'ltrace': {
                command: 'ltrace',
                testArgs: ['--version'],
                capabilities: ['library-call-tracing', 'debugging'],
                category: 'debugging',
                description: 'Library call tracer'
            },

            // Fuzzing Tools
            'afl-fuzz': {
                command: 'afl-fuzz',
                testArgs: ['-h'],
                capabilities: ['fuzzing', 'vulnerability-discovery'],
                category: 'fuzzing',
                description: 'American Fuzzy Lop fuzzer'
            },

            // Lifting and Decompilation
            'retdec-decompiler': {
                command: 'retdec-decompiler',
                testArgs: ['--help'],
                capabilities: ['decompilation', 'binary-lifting', 'reverse-engineering'],
                category: 'reverse-engineering',
                description: 'RetDec decompiler'
            }
        };
    }

    async detectTool(toolName, toolDef) {
        try {
            const result = execSync(`${toolDef.command} ${toolDef.testArgs.join(' ')}`, {
                timeout: 5000,
                stdio: 'pipe',
                encoding: 'utf8'
            });
            
            return {
                name: toolName,
                available: true,
                version: this.extractVersion(result),
                command: toolDef.command,
                capabilities: toolDef.capabilities,
                category: toolDef.category,
                description: toolDef.description
            };
        } catch (error) {
            return {
                name: toolName,
                available: false,
                error: error.message,
                command: toolDef.command,
                capabilities: toolDef.capabilities,
                category: toolDef.category,
                description: toolDef.description
            };
        }
    }

    extractVersion(output) {
        // Try to extract version from common patterns
        const versionPatterns = [
            /version\s+(\d+\.\d+\.\d+)/i,
            /v(\d+\.\d+\.\d+)/i,
            /(\d+\.\d+\.\d+)/,
            /(\d+\.\d+)/
        ];

        for (const pattern of versionPatterns) {
            const match = output.match(pattern);
            if (match) {
                return match[1];
            }
        }
        return 'unknown';
    }

    async detectAllTools() {
        console.log('🔍 Detecting available security tools...');
        
        const detectionPromises = Object.entries(this.toolDefinitions).map(
            ([name, def]) => this.detectTool(name, def)
        );

        const results = await Promise.all(detectionPromises);
        
        // Organize results
        for (const result of results) {
            this.tools.set(result.name, result);
            
            // Build capability map
            for (const capability of result.capabilities) {
                if (!this.capabilities.has(capability)) {
                    this.capabilities.set(capability, []);
                }
                this.capabilities.get(capability).push(result.name);
            }
        }

        return results;
    }

    getAvailableTools() {
        return Array.from(this.tools.values()).filter(tool => tool.available);
    }

    getToolsByCapability(capability) {
        const toolNames = this.capabilities.get(capability) || [];
        return toolNames.map(name => this.tools.get(name)).filter(tool => tool && tool.available);
    }

    getToolsByCategory(category) {
        return Array.from(this.tools.values()).filter(
            tool => tool.available && tool.category === category
        );
    }

    generateCapabilityMatrix() {
        const matrix = {};
        for (const [capability, toolNames] of this.capabilities.entries()) {
            matrix[capability] = toolNames.filter(name => this.tools.get(name)?.available);
        }
        return matrix;
    }

    formatAsTable() {
        const available = this.getAvailableTools();
        const unavailable = Array.from(this.tools.values()).filter(tool => !tool.available);

        let output = '\n📊 SECURITY TOOLS STATUS\n';
        output += '=' .repeat(80) + '\n\n';

        // Available tools
        output += `✅ AVAILABLE TOOLS (${available.length})\n`;
        output += '-'.repeat(80) + '\n';
        output += 'Tool'.padEnd(20) + 'Version'.padEnd(15) + 'Category'.padEnd(20) + 'Description\n';
        output += '-'.repeat(80) + '\n';
        
        for (const tool of available.sort((a, b) => a.category.localeCompare(b.category))) {
            output += tool.name.padEnd(20) + 
                     tool.version.padEnd(15) + 
                     tool.category.padEnd(20) + 
                     tool.description + '\n';
        }

        // Unavailable tools
        if (unavailable.length > 0) {
            output += `\n❌ UNAVAILABLE TOOLS (${unavailable.length})\n`;
            output += '-'.repeat(80) + '\n';
            for (const tool of unavailable) {
                output += `${tool.name.padEnd(20)} - ${tool.description}\n`;
            }
        }

        // Capability summary
        output += '\n🎯 CAPABILITY SUMMARY\n';
        output += '-'.repeat(80) + '\n';
        const matrix = this.generateCapabilityMatrix();
        for (const [capability, tools] of Object.entries(matrix)) {
            if (tools.length > 0) {
                output += `${capability.padEnd(25)} : ${tools.join(', ')}\n`;
            }
        }

        return output;
    }

    formatAsJson() {
        return JSON.stringify({
            tools: Object.fromEntries(this.tools),
            capabilities: Object.fromEntries(this.capabilities),
            summary: {
                total: this.tools.size,
                available: this.getAvailableTools().length,
                unavailable: this.tools.size - this.getAvailableTools().length
            },
            capabilityMatrix: this.generateCapabilityMatrix()
        }, null, 2);
    }
}

// CLI Interface
async function main() {
    const args = process.argv.slice(2);
    const format = args.includes('--format') ? args[args.indexOf('--format') + 1] : 'table';
    const output = args.includes('--output') ? args[args.indexOf('--output') + 1] : null;
    const verify = args.includes('--verify');

    const detector = new ToolDetector();
    await detector.detectAllTools();

    let result;
    if (format === 'json') {
        result = detector.formatAsJson();
    } else {
        result = detector.formatAsTable();
    }

    if (output) {
        writeFileSync(output, result);
        console.log(`Results saved to: ${output}`);
    } else {
        console.log(result);
    }

    // Exit with error code if verification requested and tools are missing
    if (verify) {
        const available = detector.getAvailableTools().length;
        const total = detector.tools.size;
        const coverage = (available / total) * 100;
        
        console.log(`\n📈 Tool Coverage: ${coverage.toFixed(1)}% (${available}/${total})`);
        
        if (coverage < 50) {
            console.log('⚠️  Warning: Less than 50% of tools are available');
            process.exit(1);
        }
    }
}

if (import.meta.url === `file://${process.argv[1]}`) {
    main().catch(console.error);
}

export { ToolDetector };