#!/usr/bin/env node
/**
 * Comprehensive Unit Tests for pf Variable Interpolation and Task Parsing
 * 
 * Tests variable interpolation, parameter parsing, and task definition handling
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
class ParserTester {
    constructor() {
        this.passed = 0;
        this.failed = 0;
        this.tests = [];
    }

    async runPfParser(pfContent, action = 'list') {
        const tmpFile = join(os.tmpdir(), `pf-parser-test-${Date.now()}.pf`);
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

    async testSyntaxValid(name, pfContent) {
        await this.test(name, async () => {
            const result = await this.runPfParser(pfContent);
            if (result.code !== 0) {
                throw new Error(`Syntax validation failed: ${result.stderr || result.stdout}`);
            }
        });
    }

    async testTaskListed(name, pfContent, expectedTasks) {
        await this.test(name, async () => {
            const result = await this.runPfParser(pfContent, 'list');
            for (const task of expectedTasks) {
                if (!result.stdout.includes(task)) {
                    throw new Error(`Expected task "${task}" not found in output: ${result.stdout}`);
                }
            }
        });
    }

    async testSyntaxInvalid(name, pfContent) {
        await this.test(name, async () => {
            const result = await this.runPfParser(pfContent);
            if (result.code === 0) {
                throw new Error(`Expected syntax error but parsing succeeded`);
            }
        });
    }
}

// Test cases
async function runTests() {
    const tester = new ParserTester();
    
    console.log('🔍 pf Variable Interpolation & Task Parsing Unit Tests');
    console.log('======================================================\n');

    // ==========================================
    // SECTION 1: Basic Variable Interpolation
    // ==========================================
    console.log('\n--- Section 1: Basic Variable Interpolation ---');

    await tester.testSyntaxValid('Simple variable reference', `
task test var="value"
  describe Test simple variable
  shell echo "$var"
end
`);

    await tester.testSyntaxValid('Braced variable reference', `
task test prefix="test"
  describe Test braced variable
  shell echo "\${prefix}_suffix"
end
`);

    await tester.testSyntaxValid('Multiple variables in command', `
task test a="1" b="2" c="3"
  describe Multiple variables
  shell echo "$a $b $c"
end
`);

    await tester.testSyntaxValid('Variable in quotes', `
task test name="World"
  describe Variable in quotes
  shell echo "Hello, $name!"
end
`);

    await tester.testSyntaxValid('Variable concatenation', `
task test first="Hello" second="World"
  describe Variable concatenation
  shell echo "$first$second"
end
`);

    await tester.testSyntaxValid('Variable with underscore', `
task test my_var="value"
  describe Variable with underscore
  shell echo "$my_var"
end
`);

    await tester.testSyntaxValid('Variable with hyphen in task param', `
task test my-param="value"
  describe Variable with hyphen
  shell echo "Value: $my-param"
end
`);

    await tester.testSyntaxValid('Variable in path', `
task test dir="/home/user"
  describe Variable in path
  shell ls "$dir/files"
end
`);

    await tester.testSyntaxValid('Variable with default value pattern', `
task test opt=""
  describe Variable with empty default
  shell echo "Option: $opt"
end
`);

    // ==========================================
    // SECTION 2: Parameter Parsing
    // ==========================================
    console.log('\n--- Section 2: Parameter Parsing ---');

    await tester.testSyntaxValid('Single parameter', `
task test param="default"
  describe Single parameter
  shell echo "$param"
end
`);

    await tester.testSyntaxValid('Multiple parameters', `
task test p1="a" p2="b" p3="c"
  describe Multiple parameters
  shell echo "$p1 $p2 $p3"
end
`);

    await tester.testSyntaxValid('Parameter with quoted value', `
task test msg="Hello World"
  describe Quoted parameter value
  shell echo "$msg"
end
`);

    await tester.testSyntaxValid('Parameter with empty value', `
task test empty=""
  describe Empty parameter value
  shell echo "Empty: $empty"
end
`);

    await tester.testSyntaxValid('Parameter with numbers', `
task test num="123" port="8080"
  describe Numeric parameter values
  shell echo "$num $port"
end
`);

    await tester.testSyntaxValid('Parameter with special characters in value', `
task test url="http://example.com:8080/path"
  describe Special chars in parameter
  shell echo "$url"
end
`);

    await tester.testSyntaxValid('Parameter with hyphen in name', `
task test my-param="value"
  describe Hyphen in parameter name
  shell echo "Param: $my-param"
end
`);

    await tester.testSyntaxValid('Parameter with underscore in name', `
task test my_param="value"
  describe Underscore in parameter name
  shell echo "Param: $my_param"
end
`);

    await tester.testSyntaxValid('Mixed parameter naming styles', `
task test camelCase="a" snake_case="b" kebab-case="c"
  describe Mixed naming styles
  shell echo "$camelCase $snake_case $kebab-case"
end
`);

    // ==========================================
    // SECTION 3: Environment Variables
    // ==========================================
    console.log('\n--- Section 3: Environment Variables ---');

    await tester.testSyntaxValid('Global env var', `
env MY_VAR="global_value"

task test
  describe Use global env var
  shell echo "$MY_VAR"
end
`);

    await tester.testSyntaxValid('Multiple global env vars', `
env VAR1="value1"
env VAR2="value2"
env VAR3="value3"

task test
  describe Use multiple global env vars
  shell echo "$VAR1 $VAR2 $VAR3"
end
`);

    await tester.testSyntaxValid('Task-local env vars', `
task test
  describe Task-local env vars
  env LOCAL_VAR=local_value
  shell echo "$LOCAL_VAR"
end
`);

    await tester.testSyntaxValid('Multiple task-local env vars', `
task test
  describe Multiple task-local env vars
  env VAR1=a VAR2=b VAR3=c
  shell echo "$VAR1 $VAR2 $VAR3"
end
`);

    await tester.testSyntaxValid('Env var referencing another var', `
env BASE="/opt"

task test
  describe Env var referencing another
  env APP_DIR=$BASE/myapp
  shell echo "$APP_DIR"
end
`);

    await tester.testSyntaxValid('Env var with PATH modification', `
task test
  describe PATH modification
  env PATH=/custom/bin:$PATH
  shell echo "$PATH"
end
`);

    await tester.testSyntaxValid('Global and local env combined', `
env GLOBAL="global"

task test
  describe Global and local env
  env LOCAL="local"
  shell echo "$GLOBAL $LOCAL"
end
`);

    await tester.testSyntaxValid('Env var with equals in value', `
task test
  describe Env var with equals
  env OPTS="--flag=value"
  shell echo "$OPTS"
end
`);

    // ==========================================
    // SECTION 4: Task Definition Variations
    // ==========================================
    console.log('\n--- Section 4: Task Definition Variations ---');

    await tester.testSyntaxValid('Simple task', `
task simple
  describe Simple task
  shell echo "Simple"
end
`);

    await tester.testSyntaxValid('Task with hyphenated name', `
task my-complex-task
  describe Hyphenated task name
  shell echo "Complex"
end
`);

    await tester.testSyntaxValid('Task with underscored name', `
task my_task_name
  describe Underscored task name
  shell echo "Task"
end
`);

    await tester.testSyntaxValid('Task with numbers in name', `
task task123
  describe Task with numbers
  shell echo "123"
end
`);

    await tester.testSyntaxValid('Task with mixed naming', `
task my-task_v2
  describe Mixed naming task
  shell echo "v2"
end
`);

    await tester.testSyntaxValid('Multiple tasks', `
task first
  describe First task
  shell echo "First"
end

task second
  describe Second task
  shell echo "Second"
end

task third
  describe Third task
  shell echo "Third"
end
`);

    await tester.testTaskListed('Tasks appear in list', `
task alpha
  describe Alpha task
  shell echo "Alpha"
end

task beta
  describe Beta task
  shell echo "Beta"
end

task gamma
  describe Gamma task
  shell echo "Gamma"
end
`, ['alpha', 'beta', 'gamma']);

    await tester.testSyntaxValid('Task with only describe', `
task describe-only
  describe This task only has a description
end
`);

    await tester.testSyntaxValid('Task with empty body', `
task empty-body
  describe Empty body task
end
`);

    // ==========================================
    // SECTION 5: Include Statements
    // ==========================================
    console.log('\n--- Section 5: Include Statements ---');

    await tester.testSyntaxValid('Single include', `
include other.pf

task main
  describe Main task
  shell echo "Main"
end
`);

    await tester.testSyntaxValid('Multiple includes', `
include tasks/common.pf
include tasks/build.pf
include tasks/deploy.pf

task main
  describe Main task
  shell echo "Main"
end
`);

    await tester.testSyntaxValid('Include with relative path', `
include ./lib/helpers.pf

task main
  describe Main task
  shell echo "Main"
end
`);

    await tester.testSyntaxValid('Include with nested path', `
include path/to/nested/tasks.pf

task main
  describe Main task
  shell echo "Main"
end
`);

    // ==========================================
    // SECTION 6: Control Flow with Variables
    // ==========================================
    console.log('\n--- Section 6: Control Flow with Variables ---');

    await tester.testSyntaxValid('If with variable comparison', `
task test mode="dev"
  describe If with variable comparison
  if $mode == "dev"
    shell echo "Development"
  end
end
`);

    await tester.testSyntaxValid('If-else with variable', `
task test env="prod"
  describe If-else with variable
  if $env == "dev"
    shell echo "Development"
  else
    shell echo "Production"
  end
end
`);

    await tester.testSyntaxValid('Nested if with variables', `
task test level="1" sub="a"
  describe Nested if with variables
  if $level == "1"
    if $sub == "a"
      shell echo "Level 1, Sub A"
    else
      shell echo "Level 1, Sub B"
    end
  else
    shell echo "Other level"
  end
end
`);

    await tester.testSyntaxValid('For loop with variable', `
task test items="a,b,c"
  describe For loop with variable
  for item in $items
    shell echo "$item"
  end
end
`);

    await tester.testSyntaxValid('For loop with array', `
task test
  describe For loop with array
  for item in ["one", "two", "three"]
    shell echo "$item"
  end
end
`);

    await tester.testSyntaxValid('Variable in for loop body', `
task test prefix="item"
  describe Variable in for loop body
  for num in ["1", "2", "3"]
    shell echo "$prefix-$num"
  end
end
`);

    // ==========================================
    // SECTION 7: Comments and Whitespace
    // ==========================================
    console.log('\n--- Section 7: Comments and Whitespace ---');

    await tester.testSyntaxValid('Task with comments', `
# Top level comment
task test
  # Comment inside task
  describe Task with comments
  shell echo "Hello" # Inline comment
end
# Bottom comment
`);

    await tester.testSyntaxValid('Multiple blank lines', `
task first
  describe First task
  shell echo "First"
end


task second
  describe Second task
  shell echo "Second"
end
`);

    await tester.testSyntaxValid('Tab indentation', `
task test
	describe Tab indented task
	shell echo "Tab"
end
`);

    await tester.testSyntaxValid('Mixed indentation', `
task test
  describe Mixed indent
	shell echo "Tab here"
  shell echo "Space here"
    shell echo "More spaces"
end
`);

    await tester.testSyntaxValid('Trailing whitespace', `
task test   
  describe Trailing whitespace   
  shell echo "Hello"   
end
`);

    // ==========================================
    // SECTION 8: Complex Parameter Scenarios
    // ==========================================
    console.log('\n--- Section 8: Complex Parameter Scenarios ---');

    await tester.testSyntaxValid('Many parameters', `
task deploy host="localhost" port="8080" user="admin" password="" env="dev" debug="true"
  describe Many parameters
  shell echo "$host:$port $user $env $debug"
end
`);

    await tester.testSyntaxValid('Parameter with file path', `
task build src="./src" out="./dist" config="./config.json"
  describe Parameters with file paths
  shell echo "$src -> $out using $config"
end
`);

    await tester.testSyntaxValid('Parameter with URL', `
task fetch url="https://api.example.com/v1/data" token=""
  describe Parameter with URL
  shell curl "$url" -H "Authorization: $token"
end
`);

    await tester.testSyntaxValid('Parameter used in multiple places', `
task test name="World"
  describe Parameter used multiple times
  shell echo "Hello, $name!"
  shell echo "$name says hi"
  shell echo "Goodbye, $name!"
end
`);

    await tester.testSyntaxValid('Parameter overriding env var', `
env DEFAULT="global"

task test DEFAULT="local"
  describe Parameter overriding env
  shell echo "$DEFAULT"
end
`);

    // ==========================================
    // SECTION 9: Edge Cases
    // ==========================================
    console.log('\n--- Section 9: Edge Cases ---');

    await tester.testSyntaxValid('Very long parameter value', `
task test long="This is a very long parameter value that contains many words and should still be handled correctly by the parser without any issues"
  describe Long parameter value
  shell echo "$long"
end
`);

    await tester.testSyntaxValid('Parameter with newline escape', `
task test msg="Line 1\\nLine 2"
  describe Parameter with newline
  shell echo -e "$msg"
end
`);

    await tester.testSyntaxValid('Special shell characters', `
task test
  describe Special shell characters
  shell echo 'Single quotes'
  shell echo "Double quotes"
  shell echo "Dollar: \\$"
  shell echo "Backtick: \\\`date\\\`"
end
`);

    await tester.testSyntaxValid('Unicode in parameter', `
task test emoji="🎉" text="日本語"
  describe Unicode in parameter
  shell echo "$emoji $text"
end
`);

    await tester.testSyntaxValid('Empty task name parts', `
task a-b-c
  describe Hyphen separated name parts
  shell echo "Works"
end
`);

    await tester.testSyntaxValid('Numeric-like task name', `
task v1-0-0
  describe Version-like task name
  shell echo "Version 1.0.0"
end
`);

    // ==========================================
    // SECTION 10: Invalid Syntax Detection
    // ==========================================
    console.log('\n--- Section 10: Invalid Syntax Detection ---');

    await tester.testSyntaxInvalid('Missing end keyword', `
task broken
  describe Missing end
  shell echo "broken"
`);

    await tester.testSyntaxInvalid('Task without name', `
task
  describe No name task
  shell echo "broken"
end
`);

    await tester.testSyntaxInvalid('Unclosed if statement', `
task broken
  describe Unclosed if
  if $var == "value"
    shell echo "broken"
end
`);

    await tester.testSyntaxInvalid('Unclosed for loop', `
task broken
  describe Unclosed for
  for item in ["a", "b"]
    shell echo "$item"
end
`);

    await tester.testSyntaxInvalid('Invalid parameter syntax', `
task broken invalid param
  describe Invalid params
  shell echo "broken"
end
`);

    // Print summary
    console.log('\n=============================');
    console.log('📊 Parser Test Results');
    console.log('=============================');
    console.log(`✅ Passed: ${tester.passed}`);
    console.log(`❌ Failed: ${tester.failed}`);
    console.log(`📈 Success Rate: ${Math.round((tester.passed / (tester.passed + tester.failed)) * 100)}%`);

    if (tester.failed === 0) {
        console.log('\n🎉 All parser tests passed!');
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

export { runTests, ParserTester };
