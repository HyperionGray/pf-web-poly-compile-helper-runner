#!/usr/bin/env node
/**
 * Unit Tests for pf Containerization Module
 * 
 * Tests automatic containerization, project detection, and retry mechanisms.
 */

import { spawn, execSync } from 'child_process';
import { promises as fs } from 'fs';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';
import os from 'os';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const projectRoot = join(__dirname, '../..');
const pfRunnerDir = join(projectRoot, 'pf-runner');

// Test utilities
class ContainerizationTester {
    constructor() {
        this.passed = 0;
        this.failed = 0;
        this.tests = [];
    }

    async runPython(script, args = []) {
        return new Promise((resolve, reject) => {
            const proc = spawn('python3', [script, ...args], {
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

            proc.on('close', (code) => {
                resolve({ code, stdout: stdout.trim(), stderr: stderr.trim() });
            });

            proc.on('error', (error) => {
                reject(error);
            });
        });
    }

    async runPfParser(pfContent, action = 'list') {
        const tmpFile = join(os.tmpdir(), `pf-container-test-${Date.now()}.pf`);
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

    async createTempProject(type) {
        const tmpDir = await fs.mkdtemp(join(os.tmpdir(), 'pf-project-'));
        
        switch (type) {
            case 'node':
                await fs.writeFile(join(tmpDir, 'package.json'), JSON.stringify({
                    name: 'test-app',
                    version: '1.0.0',
                    main: 'index.js',
                    scripts: {
                        start: 'node index.js',
                        build: 'echo "Building..."'
                    },
                    dependencies: {}
                }, null, 2));
                await fs.writeFile(join(tmpDir, 'index.js'), 'console.log("Hello");');
                break;
                
            case 'python':
                await fs.writeFile(join(tmpDir, 'requirements.txt'), 'flask\nrequests\n');
                await fs.writeFile(join(tmpDir, 'main.py'), 'print("Hello")');
                break;
                
            case 'rust':
                await fs.writeFile(join(tmpDir, 'Cargo.toml'), `
[package]
name = "test-app"
version = "0.1.0"
edition = "2021"

[dependencies]
`);
                await fs.mkdir(join(tmpDir, 'src'));
                await fs.writeFile(join(tmpDir, 'src', 'main.rs'), 'fn main() { println!("Hello"); }');
                break;
                
            case 'go':
                await fs.writeFile(join(tmpDir, 'go.mod'), 'module test-app\n\ngo 1.22\n');
                await fs.writeFile(join(tmpDir, 'main.go'), 'package main\n\nfunc main() { println("Hello") }');
                break;
                
            case 'cmake':
                await fs.writeFile(join(tmpDir, 'CMakeLists.txt'), `
cmake_minimum_required(VERSION 3.10)
project(test-app)
add_executable(main main.c)
`);
                await fs.writeFile(join(tmpDir, 'main.c'), '#include <stdio.h>\nint main() { printf("Hello\\n"); return 0; }');
                break;
                
            case 'make':
                await fs.writeFile(join(tmpDir, 'Makefile'), `
all: main

main: main.c
\tgcc -o main main.c

clean:
\trm -f main
`);
                await fs.writeFile(join(tmpDir, 'main.c'), '#include <stdio.h>\nint main() { printf("Hello\\n"); return 0; }');
                break;
                
            default:
                // Empty project
                break;
        }
        
        return tmpDir;
    }

    async cleanupTempDir(dir) {
        try {
            await fs.rm(dir, { recursive: true, force: true });
        } catch {}
    }

    async test(name, testFn) {
        let testPassed = true;
        try {
            console.log(`\n🧪 Testing: ${name}`);
            await testFn();
            console.log(`✅ PASS: ${name}`);
            this.passed++;
        } catch (error) {
            console.log(`❌ FAIL: ${name}`);
            console.log(`   Error: ${error.message}`);
            this.failed++;
            testPassed = false;
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
}

// Test cases
async function runTests() {
    const tester = new ContainerizationTester();
    
    console.log('🔍 pf Containerization Unit Tests');
    console.log('===================================\n');

    // ==========================================
    // SECTION 1: Project Detection
    // ==========================================
    console.log('\n--- Section 1: Project Detection ---');

    await tester.test('Detect Node.js project', async () => {
        const tmpDir = await tester.createTempProject('node');
        try {
            const result = await tester.runPython('pf_containerize.py', [tmpDir, '--dockerfile-only']);
            if (!result.stdout.includes('node') && !result.stdout.includes('FROM')) {
                throw new Error('Node.js project not detected correctly');
            }
        } finally {
            await tester.cleanupTempDir(tmpDir);
        }
    });

    await tester.test('Detect Python project', async () => {
        const tmpDir = await tester.createTempProject('python');
        try {
            const result = await tester.runPython('pf_containerize.py', [tmpDir, '--dockerfile-only']);
            if (!result.stdout.includes('python') && !result.stdout.includes('FROM')) {
                throw new Error('Python project not detected correctly');
            }
        } finally {
            await tester.cleanupTempDir(tmpDir);
        }
    });

    await tester.test('Detect Rust project', async () => {
        const tmpDir = await tester.createTempProject('rust');
        try {
            const result = await tester.runPython('pf_containerize.py', [tmpDir, '--dockerfile-only']);
            if (!result.stdout.includes('rust') && !result.stdout.includes('cargo') && !result.stdout.includes('FROM')) {
                throw new Error('Rust project not detected correctly');
            }
        } finally {
            await tester.cleanupTempDir(tmpDir);
        }
    });

    await tester.test('Detect Go project', async () => {
        const tmpDir = await tester.createTempProject('go');
        try {
            const result = await tester.runPython('pf_containerize.py', [tmpDir, '--dockerfile-only']);
            if (!result.stdout.includes('go') && !result.stdout.includes('FROM')) {
                throw new Error('Go project not detected correctly');
            }
        } finally {
            await tester.cleanupTempDir(tmpDir);
        }
    });

    await tester.test('Detect CMake project', async () => {
        const tmpDir = await tester.createTempProject('cmake');
        try {
            const result = await tester.runPython('pf_containerize.py', [tmpDir, '--dockerfile-only']);
            if (!result.stdout.includes('cmake') && !result.stdout.includes('FROM')) {
                throw new Error('CMake project not detected correctly');
            }
        } finally {
            await tester.cleanupTempDir(tmpDir);
        }
    });

    // ==========================================
    // SECTION 2: Dockerfile Generation
    // ==========================================
    console.log('\n--- Section 2: Dockerfile Generation ---');

    await tester.test('Generate Dockerfile with FROM directive', async () => {
        const tmpDir = await tester.createTempProject('node');
        try {
            const result = await tester.runPython('pf_containerize.py', [tmpDir, '--dockerfile-only']);
            if (!result.stdout.includes('FROM ')) {
                throw new Error('Dockerfile missing FROM directive');
            }
        } finally {
            await tester.cleanupTempDir(tmpDir);
        }
    });

    await tester.test('Generate Dockerfile with WORKDIR', async () => {
        const tmpDir = await tester.createTempProject('python');
        try {
            const result = await tester.runPython('pf_containerize.py', [tmpDir, '--dockerfile-only']);
            if (!result.stdout.includes('WORKDIR')) {
                throw new Error('Dockerfile missing WORKDIR directive');
            }
        } finally {
            await tester.cleanupTempDir(tmpDir);
        }
    });

    await tester.test('Generate Dockerfile with COPY', async () => {
        const tmpDir = await tester.createTempProject('go');
        try {
            const result = await tester.runPython('pf_containerize.py', [tmpDir, '--dockerfile-only']);
            if (!result.stdout.includes('COPY')) {
                throw new Error('Dockerfile missing COPY directive');
            }
        } finally {
            await tester.cleanupTempDir(tmpDir);
        }
    });

    await tester.test('Generate Dockerfile with CMD', async () => {
        const tmpDir = await tester.createTempProject('node');
        try {
            const result = await tester.runPython('pf_containerize.py', [tmpDir, '--dockerfile-only']);
            if (!result.stdout.includes('CMD')) {
                throw new Error('Dockerfile missing CMD directive');
            }
        } finally {
            await tester.cleanupTempDir(tmpDir);
        }
    });

    await tester.test('Apply install-hint-deps', async () => {
        const tmpDir = await tester.createTempProject('make');
        try {
            const result = await tester.runPython('pf_containerize.py', [
                tmpDir, 
                '--dockerfile-only',
                '--install-hint-deps=libssl-dev libcurl4-openssl-dev'
            ]);
            if (!result.stdout.includes('libssl-dev') || !result.stdout.includes('libcurl4-openssl-dev')) {
                throw new Error('Install hint deps not applied');
            }
        } finally {
            await tester.cleanupTempDir(tmpDir);
        }
    });

    // ==========================================
    // SECTION 3: Quadlet Generation
    // ==========================================
    console.log('\n--- Section 3: Quadlet Generation ---');

    await tester.test('Generate Quadlet container file', async () => {
        const tmpDir = await tester.createTempProject('node');
        try {
            const result = await tester.runPython('pf_containerize.py', [
                tmpDir, 
                '--quadlet-only',
                '--image-name=localhost/test-app:latest'
            ]);
            if (!result.stdout.includes('[Container]')) {
                throw new Error('Quadlet file missing [Container] section');
            }
            if (!result.stdout.includes('[Unit]')) {
                throw new Error('Quadlet file missing [Unit] section');
            }
            if (!result.stdout.includes('[Install]')) {
                throw new Error('Quadlet file missing [Install] section');
            }
        } finally {
            await tester.cleanupTempDir(tmpDir);
        }
    });

    await tester.test('Quadlet includes restart policy', async () => {
        const tmpDir = await tester.createTempProject('python');
        try {
            const result = await tester.runPython('pf_containerize.py', [
                tmpDir, 
                '--quadlet-only',
                '--image-name=localhost/test-app:latest'
            ]);
            if (!result.stdout.includes('Restart=')) {
                throw new Error('Quadlet file missing restart policy');
            }
        } finally {
            await tester.cleanupTempDir(tmpDir);
        }
    });

    await tester.test('Quadlet includes health check', async () => {
        const tmpDir = await tester.createTempProject('go');
        try {
            const result = await tester.runPython('pf_containerize.py', [
                tmpDir, 
                '--quadlet-only',
                '--image-name=localhost/test-app:latest'
            ]);
            if (!result.stdout.includes('HealthCmd')) {
                throw new Error('Quadlet file missing health check');
            }
        } finally {
            await tester.cleanupTempDir(tmpDir);
        }
    });

    // ==========================================
    // SECTION 4: pf Syntax Integration
    // ==========================================
    console.log('\n--- Section 4: pf Syntax Integration ---');

    await tester.testSyntaxValid('Basic containerize command', `
task build-container
  describe Build container for project
  containerize
end
`);

    await tester.testSyntaxValid('Containerize with image name', `
task build-container-named
  describe Build container with custom name
  containerize image=myapp tag=v1.0.0
end
`);

    await tester.testSyntaxValid('Containerize with hints', `
task build-container-hints
  describe Build container with hints
  containerize install_deps="libssl-dev" main_bin="./build/app" port=8080
end
`);

    await tester.testSyntaxValid('Containerize dockerfile-only', `
task generate-dockerfile
  describe Generate Dockerfile only
  containerize dockerfile_only=true
end
`);

    await tester.testSyntaxValid('Containerize quadlet-only', `
task generate-quadlet
  describe Generate Quadlet files only
  containerize quadlet_only=true image=myapp:latest
end
`);

    await tester.testSyntaxValid('Auto_container alias', `
task auto-container
  describe Auto containerize
  auto_container dir=./myproject
end
`);

    // ==========================================
    // SECTION 5: Autobuild with Retry
    // ==========================================
    console.log('\n--- Section 5: Autobuild with Retry ---');

    await tester.testSyntaxValid('Basic autobuild_retry', `
task build-retry
  describe Build with retry
  autobuild_retry
end
`);

    await tester.testSyntaxValid('Autobuild retry with options', `
task build-retry-opts
  describe Build with retry options
  autobuild_retry max_retries=5 initial_delay=2 max_delay=60
end
`);

    await tester.testSyntaxValid('Autobuild retry with build options', `
task build-retry-full
  describe Full build with retry
  autobuild_retry dir=./src jobs=8 release=true target=myapp
end
`);

    await tester.testSyntaxValid('Auto_build_retry alias', `
task auto-build-retry
  describe Auto build with retry
  auto_build_retry max_retries=3
end
`);

    // ==========================================
    // SECTION 6: Combined Workflows
    // ==========================================
    console.log('\n--- Section 6: Combined Workflows ---');

    await tester.testSyntaxValid('Build and containerize pipeline', `
task ci-pipeline
  describe Full CI pipeline
  autobuild_retry max_retries=3
  containerize image=myapp tag=latest
end
`);

    await tester.testSyntaxValid('Multi-stage container build', `
task multi-container
  describe Multi-stage container
  shell echo "Stage 1: Build"
  autobuild release=true
  shell echo "Stage 2: Containerize"
  containerize image=myapp tag=release
end
`);

    await tester.testSyntaxValid('Conditional containerization', `
task conditional-container mode="dev"
  describe Conditional container build
  if $mode == "production"
    autobuild release=true
    containerize image=myapp tag=prod
  else
    autobuild
    containerize image=myapp tag=dev
  end
end
`);

    // Print summary
    console.log('\n================================');
    console.log('📊 Containerization Test Results');
    console.log('================================');
    console.log(`✅ Passed: ${tester.passed}`);
    console.log(`❌ Failed: ${tester.failed}`);
    console.log(`📈 Success Rate: ${Math.round((tester.passed / (tester.passed + tester.failed)) * 100)}%`);

    if (tester.failed === 0) {
        console.log('\n🎉 All containerization tests passed!');
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

export { runTests, ContainerizationTester };
