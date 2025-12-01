#!/usr/bin/env node
/**
 * Comprehensive Unit Tests for pf Grammar and Parsing
 * 
 * Tests the grammar constructs defined in pf.lark and parsing logic in pf_parser.py
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
class GrammarTester {
    constructor() {
        this.passed = 0;
        this.failed = 0;
        this.tests = [];
    }

    async runPfParser(pfContent, action = 'list') {
        const tmpFile = join(os.tmpdir(), `pf-test-${Date.now()}.pf`);
        await fs.writeFile(tmpFile, pfContent, 'utf-8');
        
        return new Promise((resolve, reject) => {
            const proc = spawn('python3', ['pf_parser.py', action, `--file=${tmpFile}`], {
                cwd: pfRunnerDir,
                stdio: ['pipe', 'pipe', 'pipe'],
                timeout: 10000
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

    async test(name, testFn) {
        let testPassed = false;
        try {
            console.log(`\n🧪 Testing: ${name}`);
            await testFn();
            console.log(`✅ PASS: ${name}`);
            this.passed++;
            testPassed = true;
        } catch (error) {
            console.log(`❌ FAIL: ${name}`);
            console.log(`   Error: ${error.message}`);
            this.failed++;
        }
        this.tests.push({ name, passed: testPassed });
    }

    async testValidSyntax(name, pfContent) {
        await this.test(name, async () => {
            const result = await this.runPfParser(pfContent);
            if (result.code !== 0) {
                throw new Error(`Expected valid syntax but parser failed: ${result.stderr || result.stdout}`);
            }
        });
    }

    async testInvalidSyntax(name, pfContent, expectedError = null) {
        await this.test(name, async () => {
            const result = await this.runPfParser(pfContent);
            if (result.code === 0) {
                throw new Error(`Expected invalid syntax but parser succeeded`);
            }
            if (expectedError && !result.stderr.includes(expectedError) && !result.stdout.includes(expectedError)) {
                throw new Error(`Expected error containing "${expectedError}" but got: ${result.stderr || result.stdout}`);
            }
        });
    }
}

// Test cases
async function runTests() {
    const tester = new GrammarTester();
    
    console.log('🔍 pf Grammar Unit Tests');
    console.log('========================\n');

    // ==========================================
    // SECTION 1: Basic Task Definitions
    // ==========================================
    console.log('\n--- Section 1: Basic Task Definitions ---');

    await tester.testValidSyntax('Simple task definition', `
task hello
  describe Hello world task
  shell echo "Hello World"
end
`);

    await tester.testValidSyntax('Task with multiple shell commands', `
task multi-cmd
  describe Multiple commands
  shell echo "First"
  shell echo "Second"
  shell echo "Third"
end
`);

    await tester.testValidSyntax('Task with hyphens in name', `
task my-complex-task-name
  describe Task with hyphens
  shell echo "Working"
end
`);

    await tester.testValidSyntax('Task with underscores in name', `
task my_task_name
  describe Task with underscores
  shell echo "Working"
end
`);

    await tester.testValidSyntax('Multiple tasks in one file', `
task task1
  describe First task
  shell echo "Task 1"
end

task task2
  describe Second task
  shell echo "Task 2"
end

task task3
  describe Third task
  shell echo "Task 3"
end
`);

    // ==========================================
    // SECTION 2: Task Parameters
    // ==========================================
    console.log('\n--- Section 2: Task Parameters ---');

    await tester.testValidSyntax('Task with single parameter', `
task greet name="World"
  describe Greet someone
  shell echo "Hello $name"
end
`);

    await tester.testValidSyntax('Task with multiple parameters', `
task deploy env="dev" version="1.0" port="8080"
  describe Deploy application
  shell echo "Deploying $version to $env on port $port"
end
`);

    await tester.testValidSyntax('Task with empty parameter value', `
task optional-param value=""
  describe Task with empty default
  shell echo "Value: $value"
end
`);

    await tester.testValidSyntax('Task with quoted parameter containing spaces', `
task message text="Hello World"
  describe Message with spaces
  shell echo "$text"
end
`);

    await tester.testValidSyntax('Task with parameter containing special chars', `
task special chars="hello-world_123"
  describe Special chars in param
  shell echo "$chars"
end
`);

    // ==========================================
    // SECTION 3: Environment Variables
    // ==========================================
    console.log('\n--- Section 3: Environment Variables ---');

    await tester.testValidSyntax('Global environment variable', `
env PROJECT_NAME="MyProject"

task show-env
  describe Show environment
  shell echo "$PROJECT_NAME"
end
`);

    await tester.testValidSyntax('Multiple global env vars', `
env VAR1="value1"
env VAR2="value2"
env VAR3="value3"

task show-all
  describe Show all env vars
  shell echo "$VAR1 $VAR2 $VAR3"
end
`);

    await tester.testValidSyntax('Task-local environment variables', `
task build
  describe Build with env
  env CC=gcc CFLAGS="-O2"
  shell $CC $CFLAGS -o out main.c
end
`);

    await tester.testValidSyntax('Multiple env statements in task', `
task complex-env
  describe Complex env setup
  env PATH=/custom/bin:$PATH
  env CC=clang
  env CFLAGS="-Wall -Werror"
  shell echo "$CC $CFLAGS"
end
`);

    // ==========================================
    // SECTION 4: Shell Languages (Polyglot)
    // ==========================================
    console.log('\n--- Section 4: Shell Languages (Polyglot) ---');

    await tester.testValidSyntax('Python shell language', `
task python-demo
  describe Run Python
  shell_lang python
  shell print("Hello from Python")
  shell import sys; print(sys.version)
end
`);

    await tester.testValidSyntax('Node shell language', `
task node-demo
  describe Run Node.js
  shell_lang node
  shell console.log("Hello from Node")
  shell console.log(process.version)
end
`);

    await tester.testValidSyntax('Ruby shell language', `
task ruby-demo
  describe Run Ruby
  shell_lang ruby
  shell puts "Hello from Ruby"
  shell puts RUBY_VERSION
end
`);

    await tester.testValidSyntax('Go shell language', `
task go-demo
  describe Run Go
  shell_lang go
  shell fmt.Println("Hello from Go")
end
`);

    await tester.testValidSyntax('Multiple shell languages in file', `
task python-part
  describe Python task
  shell_lang python
  shell print("Python")
end

task node-part
  describe Node task
  shell_lang node
  shell console.log("Node")
end

task bash-part
  describe Bash task
  shell_lang bash
  shell echo "Bash"
end
`);

    // ==========================================
    // SECTION 5: Variable Interpolation
    // ==========================================
    console.log('\n--- Section 5: Variable Interpolation ---');

    await tester.testValidSyntax('Simple variable interpolation', `
task vars name="test"
  describe Variable interpolation
  shell echo "Name: $name"
end
`);

    await tester.testValidSyntax('Braced variable interpolation', `
task vars-braced prefix="test"
  describe Braced variable interpolation
  shell echo "File: \${prefix}_file.txt"
end
`);

    await tester.testValidSyntax('Multiple variables in command', `
task multi-vars a="1" b="2" c="3"
  describe Multiple variables
  shell echo "$a + $b + $c"
end
`);

    await tester.testValidSyntax('Variables with env vars combined', `
env PROJECT="myproject"

task combined name="default"
  describe Combined vars
  shell echo "$PROJECT: $name"
end
`);

    // ==========================================
    // SECTION 6: Control Flow - If Statements
    // ==========================================
    console.log('\n--- Section 6: Control Flow - If Statements ---');

    await tester.testValidSyntax('If with variable equals', `
task conditional mode="dev"
  describe Conditional
  if $mode == "dev"
    shell echo "Development"
  end
end
`);

    await tester.testValidSyntax('If with else', `
task if-else mode="prod"
  describe If-else
  if $mode == "dev"
    shell echo "Development"
  else
    shell echo "Production"
  end
end
`);

    await tester.testValidSyntax('If with variable exists check', `
task check-var debug="true"
  describe Variable check
  if $debug
    shell echo "Debug enabled"
  end
end
`);

    await tester.testValidSyntax('If with command success check', `
task check-cmd
  describe Command check
  if \`which gcc\`
    shell echo "GCC found"
  else
    shell echo "GCC not found"
  end
end
`);

    await tester.testValidSyntax('Nested if statements', `
task nested env="dev" debug="true"
  describe Nested ifs
  if $env == "dev"
    if $debug
      shell echo "Dev debug mode"
    else
      shell echo "Dev normal mode"
    end
  else
    shell echo "Production"
  end
end
`);

    await tester.testValidSyntax('If with not equals operator', `
task not-equals mode="prod"
  describe Not equals
  if $mode != "dev"
    shell echo "Not development"
  end
end
`);

    // ==========================================
    // SECTION 7: Control Flow - For Loops
    // ==========================================
    console.log('\n--- Section 7: Control Flow - For Loops ---');

    await tester.testValidSyntax('For loop with array', `
task loop-array
  describe Loop over array
  for item in ["a", "b", "c"]
    shell echo "Item: $item"
  end
end
`);

    await tester.testValidSyntax('For loop with files', `
task process-files
  describe Process files
  for f in ["file1.txt", "file2.txt", "file3.txt"]
    shell cat $f
  end
end
`);

    await tester.testValidSyntax('For loop with variable', `
task loop-var items="a,b,c"
  describe Loop over variable
  for item in $items
    shell echo "$item"
  end
end
`);

    await tester.testValidSyntax('Nested for loops', `
task nested-loops
  describe Nested for loops
  for i in ["1", "2"]
    for j in ["a", "b"]
      shell echo "$i-$j"
    end
  end
end
`);

    await tester.testValidSyntax('For loop with single item', `
task single-item
  describe Single item loop
  for item in ["only-one"]
    shell echo "$item"
  end
end
`);

    // ==========================================
    // SECTION 8: Build System Helpers
    // ==========================================
    console.log('\n--- Section 8: Build System Helpers ---');

    await tester.testValidSyntax('Makefile build helper', `
task build-make
  describe Build with Make
  makefile clean all
end
`);

    await tester.testValidSyntax('Make with arguments', `
task make-args
  describe Make with args
  make install PREFIX=/usr/local
end
`);

    await tester.testValidSyntax('CMake build helper', `
task build-cmake
  describe Build with CMake
  cmake -DCMAKE_BUILD_TYPE=Release
end
`);

    await tester.testValidSyntax('Meson build helper', `
task build-meson
  describe Build with Meson
  meson setup builddir
  ninja -C builddir
end
`);

    await tester.testValidSyntax('Cargo build helper', `
task build-cargo
  describe Build with Cargo
  cargo build --release
  cargo test
end
`);

    await tester.testValidSyntax('Go build helper', `
task build-go
  describe Build with Go
  go_build -o myapp main.go
end
`);

    await tester.testValidSyntax('Configure helper', `
task build-configure
  describe Build with configure
  configure --prefix=/usr/local --enable-shared
end
`);

    await tester.testValidSyntax('Just build helper', `
task build-just
  describe Build with Just
  justfile build
  just test
end
`);

    await tester.testValidSyntax('Autobuild helper', `
task auto
  describe Auto detect and build
  autobuild
end
`);

    await tester.testValidSyntax('Build detect helper', `
task detect
  describe Detect build system
  build_detect
end
`);

    // ==========================================
    // SECTION 9: System Operations
    // ==========================================
    console.log('\n--- Section 9: System Operations ---');

    await tester.testValidSyntax('Package install', `
task install-deps
  describe Install packages
  packages install gcc make cmake
end
`);

    await tester.testValidSyntax('Package remove', `
task remove-deps
  describe Remove packages
  packages remove old-package
end
`);

    await tester.testValidSyntax('Service start', `
task start-service
  describe Start service
  service start nginx
end
`);

    await tester.testValidSyntax('Service stop', `
task stop-service
  describe Stop service
  service stop nginx
end
`);

    await tester.testValidSyntax('Service enable', `
task enable-service
  describe Enable service
  service enable nginx
end
`);

    await tester.testValidSyntax('Service restart', `
task restart-service
  describe Restart service
  service restart nginx
end
`);

    await tester.testValidSyntax('Directory creation', `
task setup-dirs
  describe Create directories
  directory /tmp/build mode=0755
  directory /var/log/myapp
end
`);

    await tester.testValidSyntax('File copy', `
task copy-files
  describe Copy files
  copy config.conf /etc/myapp/ mode=0644 user=root group=root
end
`);

    // ==========================================
    // SECTION 10: Sync Statements
    // ==========================================
    console.log('\n--- Section 10: Sync Statements ---');

    await tester.testValidSyntax('Basic sync', `
task sync-files
  describe Sync files
  sync src="/local/path" dst="/remote/path"
end
`);

    await tester.testValidSyntax('Sync with SSH', `
task sync-remote
  describe Sync to remote
  sync src="/local/path" dst="user@host:/remote/path"
end
`);

    await tester.testValidSyntax('Sync with options', `
task sync-full
  describe Full sync options
  sync src="/local" dst="/remote" verbose recursive delete
end
`);

    // ==========================================
    // SECTION 11: Comments
    // ==========================================
    console.log('\n--- Section 11: Comments ---');

    await tester.testValidSyntax('File with comments', `
# This is a top-level comment

task example
  # Comment inside task
  describe Example task
  shell echo "Hello" # Inline comment
end

# Final comment
`);

    await tester.testValidSyntax('Multiple comments', `
# Comment 1
# Comment 2
# Comment 3

task test
  describe Test task
  # Before shell
  shell echo "Test"
  # After shell
end
`);

    // ==========================================
    // SECTION 12: Include Statements
    // ==========================================
    console.log('\n--- Section 12: Include Statements ---');

    await tester.testValidSyntax('Include statement', `
include other.pf

task main
  describe Main task
  shell echo "Main"
end
`);

    await tester.testValidSyntax('Multiple includes', `
include tasks/web.pf
include tasks/api.pf
include tasks/db.pf

task deploy-all
  describe Deploy all services
  shell echo "Deploying all"
end
`);

    // ==========================================
    // SECTION 13: Complex Combinations
    // ==========================================
    console.log('\n--- Section 13: Complex Combinations ---');

    await tester.testValidSyntax('Complex task with everything', `
env PROJECT="myproject"
env VERSION="1.0.0"

task deploy-full env="dev" region="us-east" dry_run="false"
  describe Full deployment task with all features
  env DEPLOY_ENV=$env
  env DEPLOY_REGION=$region
  
  if $dry_run == "true"
    shell echo "DRY RUN: Would deploy $PROJECT v$VERSION to $env in $region"
  else
    if $env == "prod"
      shell echo "Production deployment..."
      for svc in ["api", "web", "worker"]
        shell echo "Deploying $svc to $DEPLOY_REGION"
      end
    else
      shell echo "Development deployment..."
      shell echo "Deploying to $DEPLOY_REGION"
    end
  end
end
`);

    await tester.testValidSyntax('Multi-language file', `
task python-task
  describe Python task
  shell_lang python
  shell print("Python")
  shell import sys
  shell print(sys.version)
end

task node-task
  describe Node task
  shell_lang node
  shell console.log("Node")
  shell console.log(process.version)
end

task bash-task
  describe Bash task
  shell echo "Bash"
  shell ls -la
end
`);

    await tester.testValidSyntax('Build pipeline', `
task build-pipeline target="wasm" optimize="true"
  describe Complete build pipeline
  
  build_detect
  
  if $target == "wasm"
    shell echo "Building for WebAssembly"
    cargo build --target wasm32-unknown-unknown
  else
    shell echo "Building native"
    cargo build
  end
  
  if $optimize == "true"
    shell echo "Optimizing..."
    shell wasm-opt -O3 target/wasm32-unknown-unknown/release/app.wasm -o dist/app.wasm
  end
  
  shell echo "Build complete!"
end
`);

    // ==========================================
    // SECTION 14: Invalid Syntax Tests
    // ==========================================
    console.log('\n--- Section 14: Invalid Syntax Tests ---');

    await tester.testInvalidSyntax('Missing end keyword', `
task broken
  describe Missing end
  shell echo "broken"
`);

    await tester.testInvalidSyntax('Invalid operator in if', `
task bad-if
  describe Bad if
  if $var === "value"
    shell echo "bad"
  end
end
`);

    await tester.testInvalidSyntax('Missing in keyword in for', `
task bad-for
  describe Bad for
  for item ["a", "b"]
    shell echo $item
  end
end
`);

    await tester.testInvalidSyntax('Invalid service action', `
task bad-service
  describe Bad service
  service invalidaction nginx
end
`);

    await tester.testInvalidSyntax('Invalid packages action', `
task bad-packages
  describe Bad packages
  packages invalidaction package-name
end
`);

    // ==========================================
    // SECTION 15: Edge Cases
    // ==========================================
    console.log('\n--- Section 15: Edge Cases ---');

    await tester.testValidSyntax('Empty task body', `
task empty
  describe Empty task
end
`);

    await tester.testValidSyntax('Task with only describe', `
task describe-only
  describe Only has description
end
`);

    await tester.testValidSyntax('Very long task name', `
task this-is-a-very-long-task-name-that-should-still-work
  describe Long name task
  shell echo "Works"
end
`);

    await tester.testValidSyntax('Special characters in strings', `
task special-chars
  describe Special characters
  shell echo "Hello! @#$%^&*(){}[]|:;<>?,."
end
`);

    await tester.testValidSyntax('Escaped quotes in strings', `
task escaped
  describe Escaped quotes
  shell echo "He said \\"Hello\\""
end
`);

    await tester.testValidSyntax('Tab indentation', `
task tabs
	describe Tab indented
	shell echo "Using tabs"
end
`);

    await tester.testValidSyntax('Mixed indentation', `
task mixed
  describe Mixed indentation
	shell echo "Tab here"
  shell echo "Space here"
end
`);

    // Print summary
    console.log('\n=============================');
    console.log('📊 Test Results');
    console.log('=============================');
    console.log(`✅ Passed: ${tester.passed}`);
    console.log(`❌ Failed: ${tester.failed}`);
    console.log(`📈 Success Rate: ${Math.round((tester.passed / (tester.passed + tester.failed)) * 100)}%`);

    if (tester.failed === 0) {
        console.log('\n🎉 All grammar tests passed!');
    } else {
        console.log('\n⚠️  Some tests failed. Please review the grammar implementation.');
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

export { runTests, GrammarTester };
