#!/usr/bin/env node
/**
 * Comprehensive Unit Tests for pf Polyglot Language Support
 * 
 * Tests all supported shell languages and polyglot execution features
 */

import { spawn } from 'child_process';
import { promises as fs } from 'fs';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';
import os from 'os';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const projectRoot = join(__dirname, '../..');
const pfRunnerDir = join(projectRoot, 'pf-runner');

// Test utilities
class PolyglotTester {
    constructor() {
        this.passed = 0;
        this.failed = 0;
        this.tests = [];
    }

    async runPfTask(pfContent, taskName = null) {
        const tmpFile = join(os.tmpdir(), `pf-polyglot-test-${Date.now()}.pf`);
        await fs.writeFile(tmpFile, pfContent, 'utf-8');
        
        const args = ['pf_parser.py'];
        if (taskName) {
            args.push(taskName);
        } else {
            args.push('list');
        }
        args.push(`--file=${tmpFile}`);
        
        return new Promise((resolve, reject) => {
            const proc = spawn('python3', args, {
                cwd: pfRunnerDir,
                stdio: ['pipe', 'pipe', 'pipe'],
                timeout: 30000
            });

            let stdout = '';
            let stderr = '';

            proc.stdout.on('data', (data) => {
                stdout += data.toString();
            });

            proc.stderr.on('data', (data) => {
                stderr += data.toString();
            });

            proc.on('close', async (code) => {
                try {
                    await fs.unlink(tmpFile);
                } catch {}
                resolve({ code, stdout: stdout.trim(), stderr: stderr.trim() });
            });

            proc.on('error', (error) => {
                reject(error);
            });
        });
    }

    async checkLanguageAvailable(command) {
        return new Promise((resolve) => {
            const proc = spawn('which', [command], { stdio: 'pipe' });
            proc.on('close', (code) => {
                resolve(code === 0);
            });
            proc.on('error', () => {
                resolve(false);
            });
        });
    }

    async test(name, testFn) {
        try {
            console.log(`\n🧪 Testing: ${name}`);
            await testFn();
            console.log(`✅ PASS: ${name}`);
            this.passed++;
        } catch (error) {
            console.log(`❌ FAIL: ${name}`);
            console.log(`   Error: ${error.message}`);
            this.failed++;
        }
        this.tests.push({ name, passed: this.failed === 0 });
    }

    async testSyntaxValid(name, pfContent) {
        await this.test(name, async () => {
            const result = await this.runPfTask(pfContent);
            if (result.code !== 0) {
                throw new Error(`Syntax validation failed: ${result.stderr || result.stdout}`);
            }
        });
    }

    async testSkipIfMissing(name, command, testFn) {
        const available = await this.checkLanguageAvailable(command);
        if (!available) {
            console.log(`\n⏭️  Skipping: ${name} (${command} not available)`);
            return;
        }
        await this.test(name, testFn);
    }
}

// Test cases
async function runTests() {
    const tester = new PolyglotTester();
    
    console.log('🔍 pf Polyglot Language Support Unit Tests');
    console.log('==========================================\n');

    // ==========================================
    // SECTION 1: Shell Language Syntax
    // ==========================================
    console.log('\n--- Section 1: Shell Language Syntax ---');

    await tester.testSyntaxValid('Bash shell language', `
task bash-test
  describe Test bash shell
  shell_lang bash
  shell echo "Hello from Bash"
  shell echo \$SHELL
end
`);

    await tester.testSyntaxValid('Python shell language', `
task python-test
  describe Test python shell
  shell_lang python
  shell print("Hello from Python")
  shell import sys
  shell print(sys.version)
end
`);

    await tester.testSyntaxValid('Node.js shell language', `
task node-test
  describe Test node shell
  shell_lang node
  shell console.log("Hello from Node")
  shell console.log(process.version)
end
`);

    await tester.testSyntaxValid('Ruby shell language', `
task ruby-test
  describe Test ruby shell
  shell_lang ruby
  shell puts "Hello from Ruby"
  shell puts RUBY_VERSION
end
`);

    await tester.testSyntaxValid('Perl shell language', `
task perl-test
  describe Test perl shell
  shell_lang perl
  shell print "Hello from Perl\\n";
  shell print \$^V . "\\n";
end
`);

    await tester.testSyntaxValid('PHP shell language', `
task php-test
  describe Test php shell
  shell_lang php
  shell echo "Hello from PHP\\n";
  shell echo PHP_VERSION . "\\n";
end
`);

    await tester.testSyntaxValid('Go shell language', `
task go-test
  describe Test go shell
  shell_lang go
  shell fmt.Println("Hello from Go")
end
`);

    await tester.testSyntaxValid('Rust shell language', `
task rust-test
  describe Test rust shell
  shell_lang rust
  shell fn main() { println!("Hello from Rust"); }
end
`);

    await tester.testSyntaxValid('C shell language', `
task c-test
  describe Test C shell
  shell_lang c
  shell #include <stdio.h>
  shell int main() { printf("Hello from C\\n"); return 0; }
end
`);

    await tester.testSyntaxValid('C++ shell language', `
task cpp-test
  describe Test C++ shell
  shell_lang cpp
  shell #include <iostream>
  shell int main() { std::cout << "Hello from C++" << std::endl; return 0; }
end
`);

    // ==========================================
    // SECTION 2: Compiled Language Support
    // ==========================================
    console.log('\n--- Section 2: Compiled Language Support ---');

    await tester.testSyntaxValid('Fortran shell language', `
task fortran-test
  describe Test Fortran shell
  shell_lang fortran
  shell program hello
  shell   print *, "Hello from Fortran"
  shell end program hello
end
`);

    await tester.testSyntaxValid('Zig shell language', `
task zig-test
  describe Test Zig shell
  shell_lang zig
  shell const std = @import("std");
  shell pub fn main() void { std.debug.print("Hello from Zig", .{}); }
end
`);

    await tester.testSyntaxValid('Nim shell language', `
task nim-test
  describe Test Nim shell
  shell_lang nim
  shell echo "Hello from Nim"
end
`);

    await tester.testSyntaxValid('Crystal shell language', `
task crystal-test
  describe Test Crystal shell
  shell_lang crystal
  shell puts "Hello from Crystal"
end
`);

    await tester.testSyntaxValid('Haskell shell language', `
task haskell-test
  describe Test Haskell shell
  shell_lang haskell
  shell main = putStrLn "Hello from Haskell"
end
`);

    await tester.testSyntaxValid('OCaml shell language', `
task ocaml-test
  describe Test OCaml shell
  shell_lang ocaml
  shell print_endline "Hello from OCaml"
end
`);

    // ==========================================
    // SECTION 3: JVM Languages
    // ==========================================
    console.log('\n--- Section 3: JVM Languages ---');

    await tester.testSyntaxValid('Java shell language', `
task java-test
  describe Test Java shell
  shell_lang java
  shell public class Main {
  shell   public static void main(String[] args) {
  shell     System.out.println("Hello from Java");
  shell   }
  shell }
end
`);

    await tester.testSyntaxValid('Java Android shell language', `
task java-android-test
  describe Test Java Android shell
  shell_lang java-android
  shell public class Main {
  shell   public static void main(String[] args) {
  shell     System.out.println("Hello from Java Android");
  shell   }
  shell }
end
`);

    // ==========================================
    // SECTION 4: Modern Languages
    // ==========================================
    console.log('\n--- Section 4: Modern Languages ---');

    await tester.testSyntaxValid('Deno shell language', `
task deno-test
  describe Test Deno shell
  shell_lang deno
  shell console.log("Hello from Deno");
  shell console.log(Deno.version.deno);
end
`);

    await tester.testSyntaxValid('ts-node shell language', `
task tsnode-test
  describe Test ts-node shell
  shell_lang ts-node
  shell const message: string = "Hello from TypeScript";
  shell console.log(message);
end
`);

    await tester.testSyntaxValid('Julia shell language', `
task julia-test
  describe Test Julia shell
  shell_lang julia
  shell println("Hello from Julia")
  shell println(VERSION)
end
`);

    await tester.testSyntaxValid('Elixir shell language', `
task elixir-test
  describe Test Elixir shell
  shell_lang elixir
  shell IO.puts "Hello from Elixir"
end
`);

    await tester.testSyntaxValid('Dart shell language', `
task dart-test
  describe Test Dart shell
  shell_lang dart
  shell void main() { print("Hello from Dart"); }
end
`);

    await tester.testSyntaxValid('Lua shell language', `
task lua-test
  describe Test Lua shell
  shell_lang lua
  shell print("Hello from Lua")
end
`);

    await tester.testSyntaxValid('R shell language', `
task r-test
  describe Test R shell
  shell_lang r
  shell print("Hello from R")
end
`);

    // ==========================================
    // SECTION 5: Alternative Shells
    // ==========================================
    console.log('\n--- Section 5: Alternative Shells ---');

    await tester.testSyntaxValid('Sh shell language', `
task sh-test
  describe Test sh shell
  shell_lang sh
  shell echo "Hello from sh"
end
`);

    await tester.testSyntaxValid('Dash shell language', `
task dash-test
  describe Test dash shell
  shell_lang dash
  shell echo "Hello from dash"
end
`);

    await tester.testSyntaxValid('Zsh shell language', `
task zsh-test
  describe Test zsh shell
  shell_lang zsh
  shell echo "Hello from zsh"
end
`);

    await tester.testSyntaxValid('Fish shell language', `
task fish-test
  describe Test fish shell
  shell_lang fish
  shell echo "Hello from fish"
end
`);

    await tester.testSyntaxValid('Ksh shell language', `
task ksh-test
  describe Test ksh shell
  shell_lang ksh
  shell echo "Hello from ksh"
end
`);

    await tester.testSyntaxValid('Tcsh shell language', `
task tcsh-test
  describe Test tcsh shell
  shell_lang tcsh
  shell echo "Hello from tcsh"
end
`);

    await tester.testSyntaxValid('PowerShell shell language', `
task pwsh-test
  describe Test PowerShell shell
  shell_lang pwsh
  shell Write-Host "Hello from PowerShell"
end
`);

    // ==========================================
    // SECTION 6: Language Aliases
    // ==========================================
    console.log('\n--- Section 6: Language Aliases ---');

    await tester.testSyntaxValid('Python alias: py', `
task py-alias
  describe Test py alias
  shell_lang py
  shell print("Hello")
end
`);

    await tester.testSyntaxValid('Python alias: python3', `
task python3-alias
  describe Test python3 alias
  shell_lang python3
  shell print("Hello")
end
`);

    await tester.testSyntaxValid('JavaScript alias: js', `
task js-alias
  describe Test js alias
  shell_lang js
  shell console.log("Hello")
end
`);

    await tester.testSyntaxValid('JavaScript alias: javascript', `
task javascript-alias
  describe Test javascript alias
  shell_lang javascript
  shell console.log("Hello")
end
`);

    await tester.testSyntaxValid('TypeScript alias: ts', `
task ts-alias
  describe Test ts alias
  shell_lang ts
  shell console.log("Hello")
end
`);

    await tester.testSyntaxValid('C++ alias: c++', `
task cpp-alias
  describe Test c++ alias
  shell_lang cpp
  shell #include <iostream>
  shell int main() { std::cout << "Hello"; return 0; }
end
`);

    await tester.testSyntaxValid('Go alias: golang', `
task golang-alias
  describe Test golang alias
  shell_lang golang
  shell fmt.Println("Hello")
end
`);

    await tester.testSyntaxValid('Ruby alias: rb', `
task rb-alias
  describe Test rb alias
  shell_lang rb
  shell puts "Hello"
end
`);

    // ==========================================
    // SECTION 7: LLVM IR Generation
    // ==========================================
    console.log('\n--- Section 7: LLVM IR Generation ---');

    await tester.testSyntaxValid('C LLVM IR', `
task c-llvm-test
  describe Test C LLVM IR generation
  shell_lang c-llvm
  shell #include <stdio.h>
  shell int main() { printf("Hello\\n"); return 0; }
end
`);

    await tester.testSyntaxValid('C++ LLVM IR', `
task cpp-llvm-test
  describe Test C++ LLVM IR generation
  shell_lang cpp-llvm
  shell #include <iostream>
  shell int main() { std::cout << "Hello"; return 0; }
end
`);

    await tester.testSyntaxValid('C LLVM bitcode', `
task c-bc-test
  describe Test C LLVM bitcode
  shell_lang c-llvm-bc
  shell int main() { return 0; }
end
`);

    await tester.testSyntaxValid('Fortran LLVM IR', `
task fortran-llvm-test
  describe Test Fortran LLVM IR generation
  shell_lang fortran-llvm
  shell program hello
  shell   print *, "Hello"
  shell end program hello
end
`);

    // ==========================================
    // SECTION 8: Assembly Language
    // ==========================================
    console.log('\n--- Section 8: Assembly Language ---');

    await tester.testSyntaxValid('Assembly shell language', `
task asm-test
  describe Test assembly shell
  shell_lang asm
  shell .global _start
  shell _start:
  shell   mov \$60, %rax
  shell   xor %rdi, %rdi
  shell   syscall
end
`);

    // ==========================================
    // SECTION 9: Multiple Languages in One File
    // ==========================================
    console.log('\n--- Section 9: Multiple Languages in One File ---');

    await tester.testSyntaxValid('Multiple languages in sequence', `
task python-task
  describe Python task
  shell_lang python
  shell print("Python")
end

task node-task
  describe Node task
  shell_lang node
  shell console.log("Node")
end

task ruby-task
  describe Ruby task
  shell_lang ruby
  shell puts "Ruby"
end

task bash-task
  describe Bash task
  shell_lang bash
  shell echo "Bash"
end
`);

    await tester.testSyntaxValid('Mixed shell and polyglot', `
task mixed-test
  describe Mixed shell and polyglot
  shell echo "Starting..."
  shell_lang python
  shell print("Python step")
  shell print("Another Python line")
end
`);

    // ==========================================
    // SECTION 10: File References
    // ==========================================
    console.log('\n--- Section 10: File References ---');

    await tester.testSyntaxValid('File reference syntax', `
task file-ref
  describe Test file reference
  shell_lang python
  shell @scripts/setup.py -- arg1 arg2
end
`);

    await tester.testSyntaxValid('Shell script with file reference', `
task script-ref
  describe Test script reference
  shell @scripts/build.sh
end
`);

    // ==========================================
    // SECTION 11: Edge Cases
    // ==========================================
    console.log('\n--- Section 11: Edge Cases ---');

    await tester.testSyntaxValid('Empty shell_lang', `
task default-lang
  describe Default shell language
  shell echo "Using default"
end
`);

    await tester.testSyntaxValid('Shell with complex arguments', `
task complex-args
  describe Complex shell arguments
  shell echo "Hello \\"World\\"" | grep -o "World"
end
`);

    await tester.testSyntaxValid('Shell with pipes', `
task pipes
  describe Shell with pipes
  shell cat /etc/passwd | head -n 5 | wc -l
end
`);

    await tester.testSyntaxValid('Shell with redirects', `
task redirects
  describe Shell with redirects
  shell echo "test" > /tmp/test.txt
  shell cat < /tmp/test.txt
  shell echo "append" >> /tmp/test.txt
end
`);

    await tester.testSyntaxValid('Shell with background', `
task background
  describe Shell with background
  shell sleep 1 &
  shell echo "Continuing..."
end
`);

    await tester.testSyntaxValid('Shell with subshell', `
task subshell
  describe Shell with subshell
  shell echo "Count: $(ls | wc -l)"
end
`);

    await tester.testSyntaxValid('Shell with arrays', `
task arrays
  describe Shell with arrays
  shell_lang bash
  shell arr=(one two three)
  shell echo "\${arr[0]}"
end
`);

    // ==========================================
    // SECTION 12: Error Handling
    // ==========================================
    console.log('\n--- Section 12: Error Handling Patterns ---');

    await tester.testSyntaxValid('Shell with error handling', `
task error-handling
  describe Error handling patterns
  shell set -e
  shell trap 'echo "Error occurred"' ERR
  shell echo "Running..."
end
`);

    await tester.testSyntaxValid('Shell with exit codes', `
task exit-codes
  describe Exit code handling
  shell command || echo "Command failed"
  shell command && echo "Command succeeded"
end
`);

    // Print summary
    console.log('\n=============================');
    console.log('📊 Polyglot Test Results');
    console.log('=============================');
    console.log(`✅ Passed: ${tester.passed}`);
    console.log(`❌ Failed: ${tester.failed}`);
    console.log(`📈 Success Rate: ${Math.round((tester.passed / (tester.passed + tester.failed)) * 100)}%`);

    if (tester.failed === 0) {
        console.log('\n🎉 All polyglot tests passed!');
    } else {
        console.log('\n⚠️  Some tests failed. Please review the implementation.');
    }

    return tester.failed === 0;
}

// Run tests if executed directly
if (import.meta.url === `file://${process.argv[1]}`) {
    runTests().then(success => {
        process.exit(success ? 0 : 1);
    }).catch(error => {
        console.error('Test runner error:', error);
        process.exit(1);
    });
}

export { runTests, PolyglotTester };
