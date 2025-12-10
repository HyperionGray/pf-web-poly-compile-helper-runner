#!/usr/bin/env node
/**
 * Tool Detection and Capability Discovery System
 * Detects available security tools and their capabilities
 * From PR #196 - Enhanced implementation
 */

import { execSync } from 'child_process';
import { writeFileSync } from 'fs';

// Tool definitions with their capabilities and detection methods
const TOOL_DEFINITIONS = {
  // Binary Analysis Tools
  checksec: {
    capabilities: ['binary-analysis', 'security-features'],
    commands: ['checksec'],
    description: 'Binary security feature checker'
  },
  readelf: {
    capabilities: ['binary-analysis', 'elf-analysis'],
    commands: ['readelf'],
    description: 'ELF file analysis tool'
  },
  objdump: {
    capabilities: ['binary-analysis', 'disassembly'],
    commands: ['objdump'],
    description: 'Object file disassembler'
  },
  nm: {
    capabilities: ['binary-analysis', 'symbol-analysis'],
    commands: ['nm'],
    description: 'Symbol table analyzer'
  },
  
  // Debuggers
  gdb: {
    capabilities: ['debugging', 'binary-analysis'],
    commands: ['gdb'],
    description: 'GNU Debugger'
  },
  lldb: {
    capabilities: ['debugging', 'binary-analysis'],
    commands: ['lldb'],
    description: 'LLVM Debugger'
  },
  pwndbg: {
    capabilities: ['debugging', 'exploit-development'],
    commands: ['gdb', '--version'],
    description: 'GDB plugin for exploit development',
    checkCommand: () => {
      try {
        // Check if gdb exists first
        execSync('which gdb 2>/dev/null', { encoding: 'utf8', stdio: 'pipe' });
        // Try to check for pwndbg config file as a simpler check
        try {
          execSync('test -f ~/.gdbinit && grep -q pwndbg ~/.gdbinit 2>/dev/null', {
            encoding: 'utf8',
            stdio: 'pipe',
            shell: true
          });
          return true;
        } catch {
          return false;
        }
      } catch {
        return false;
      }
    }
  },
  
  // Reverse Engineering
  radare2: {
    capabilities: ['reverse-engineering', 'disassembly', 'binary-analysis'],
    commands: ['radare2', '-v'],
    description: 'Reverse engineering framework'
  },
  ghidra: {
    capabilities: ['reverse-engineering', 'decompilation'],
    commands: ['ghidraRun'],
    description: 'NSA reverse engineering suite'
  },
  
  // Exploit Development
  ROPgadget: {
    capabilities: ['exploit-development', 'rop-analysis'],
    commands: ['ROPgadget'],
    description: 'ROP gadget finder'
  },
  ropper: {
    capabilities: ['exploit-development', 'rop-analysis'],
    commands: ['ropper'],
    description: 'ROP gadget finder and exploit tool'
  },
  pwntools: {
    capabilities: ['exploit-development', 'scripting'],
    commands: ['python3', '-c', 'import pwn'],
    description: 'CTF framework and exploit development library',
    checkCommand: (cmd) => {
      try {
        execSync('python3 -c "import pwn" 2>&1', { encoding: 'utf8' });
        return true;
      } catch {
        return false;
      }
    }
  },
  
  // Fuzzing
  AFL: {
    capabilities: ['fuzzing', 'testing'],
    commands: ['afl-fuzz'],
    description: 'American Fuzzy Lop fuzzer'
  },
  
  // Web Security
  curl: {
    capabilities: ['web-testing', 'http-client'],
    commands: ['curl'],
    description: 'HTTP client'
  },
  
  // System Tools
  file: {
    capabilities: ['file-analysis'],
    commands: ['file'],
    description: 'File type detection'
  },
  strings: {
    capabilities: ['binary-analysis', 'string-extraction'],
    commands: ['strings'],
    description: 'Extract printable strings from files'
  },
  ldd: {
    capabilities: ['binary-analysis', 'dependency-analysis'],
    commands: ['ldd'],
    description: 'Print shared library dependencies'
  }
};

function checkToolAvailability(toolName, definition) {
  try {
    // Use custom check command if provided
    if (definition.checkCommand) {
      return definition.checkCommand(definition.commands);
    }
    
    // Default: try to run the command
    const command = definition.commands[0];
    
    // First check if command exists using 'which'
    try {
      execSync(`which ${command} 2>/dev/null`, { encoding: 'utf8', stdio: 'pipe' });
    } catch {
      return false;
    }
    
    // Try to run the command with --version or -v
    try {
      execSync(`${command} --version 2>&1 || ${command} -v 2>&1`, {
        encoding: 'utf8',
        stdio: 'pipe',
        timeout: 2000
      });
      return true;
    } catch {
      // Some tools don't support --version, but if 'which' found them, they exist
      return true;
    }
  } catch (error) {
    return false;
  }
}

function detectTools() {
  const results = {};
  let availableCount = 0;
  
  for (const [toolName, definition] of Object.entries(TOOL_DEFINITIONS)) {
    const available = checkToolAvailability(toolName, definition);
    
    results[toolName] = {
      available,
      capabilities: definition.capabilities,
      description: definition.description
    };
    
    if (available) {
      availableCount++;
    }
  }
  
  return {
    tools: results,
    summary: {
      total: Object.keys(TOOL_DEFINITIONS).length,
      available: availableCount,
      missing: Object.keys(TOOL_DEFINITIONS).length - availableCount
    }
  };
}

function formatTable(detection) {
  const { tools, summary } = detection;
  
  let output = '\n🔍 Security Tool Detection Results\n';
  output += '═'.repeat(80) + '\n\n';
  
  output += `📊 Summary: ${summary.available}/${summary.total} tools available\n\n`;
  
  // Group by category
  const categories = {
    'Binary Analysis': [],
    'Debugging': [],
    'Reverse Engineering': [],
    'Exploit Development': [],
    'Fuzzing': [],
    'Web Security': [],
    'System Tools': []
  };
  
  for (const [name, info] of Object.entries(tools)) {
    const caps = info.capabilities;
    
    if (caps.includes('debugging')) {
      categories['Debugging'].push({ name, ...info });
    } else if (caps.includes('reverse-engineering')) {
      categories['Reverse Engineering'].push({ name, ...info });
    } else if (caps.includes('exploit-development')) {
      categories['Exploit Development'].push({ name, ...info });
    } else if (caps.includes('fuzzing')) {
      categories['Fuzzing'].push({ name, ...info });
    } else if (caps.includes('web-testing')) {
      categories['Web Security'].push({ name, ...info });
    } else if (caps.includes('binary-analysis') || caps.includes('elf-analysis')) {
      categories['Binary Analysis'].push({ name, ...info });
    } else {
      categories['System Tools'].push({ name, ...info });
    }
  }
  
  for (const [category, toolList] of Object.entries(categories)) {
    if (toolList.length === 0) continue;
    
    output += `\n${category}:\n`;
    output += '─'.repeat(80) + '\n';
    
    for (const tool of toolList) {
      const icon = tool.available ? '✅' : '❌';
      const status = tool.available ? 'Available' : 'Missing';
      output += `${icon} ${tool.name.padEnd(15)} ${status.padEnd(12)} ${tool.description}\n`;
    }
  }
  
  output += '\n' + '═'.repeat(80) + '\n';
  
  if (summary.missing > 0) {
    output += `\n⚠️  ${summary.missing} tools are missing. Install them for full functionality.\n`;
  } else {
    output += '\n✨ All tools are available! You have full functionality.\n';
  }
  
  return output;
}

function main() {
  const args = process.argv.slice(2);
  
  // Parse arguments
  const formatIndex = args.indexOf('--format');
  const format = formatIndex !== -1 ? args[formatIndex + 1] : 'table';
  
  const outputIndex = args.indexOf('--output');
  const outputFile = outputIndex !== -1 ? args[outputIndex + 1] : null;
  
  // Detect tools
  const detection = detectTools();
  
  // Format output
  let output;
  if (format === 'json') {
    output = JSON.stringify(detection, null, 2);
  } else {
    output = formatTable(detection);
  }
  
  // Write output
  if (outputFile) {
    writeFileSync(outputFile, output);
    console.log(`✅ Tool detection results written to: ${outputFile}`);
  } else {
    console.log(output);
  }
}

main();
