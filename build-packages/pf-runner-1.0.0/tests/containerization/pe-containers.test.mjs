#!/usr/bin/env node
/**
 * Unit Tests for PE Containers Module
 * 
 * Tests PE execution container configurations, Dockerfile validation,
 * and pf task syntax for VMKit, ReactOS, and macOS containers.
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
const dockerfilesDir = join(projectRoot, 'containers/dockerfiles');

// Test utilities
class PEContainersTester {
    constructor() {
        this.passed = 0;
        this.failed = 0;
        this.tests = [];
    }

    async runPfParser(pfContent, action = 'list') {
        const tmpFile = join(os.tmpdir(), `pf-pe-test-${Date.now()}.pf`);
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

    async fileExists(path) {
        try {
            await fs.access(path);
            return true;
        } catch {
            return false;
        }
    }

    async readFile(path) {
        return await fs.readFile(path, 'utf-8');
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
            try {
                const result = await this.runPfParser(pfContent);
                if (result.code !== 0) {
                    // Check if failure is due to missing dependencies (not syntax error)
                    if (result.stderr && result.stderr.includes('ModuleNotFoundError')) {
                        console.log(`   (Skipped: parser dependency missing)`);
                        return; // Skip test if dependencies are missing
                    }
                    throw new Error(`Syntax validation failed: ${result.stderr || result.stdout}`);
                }
            } catch (err) {
                if (err.message && err.message.includes('spawn python3')) {
                    console.log(`   (Skipped: python3 not available)`);
                    return;
                }
                throw err;
            }
        });
    }
}

// Test cases
async function runTests() {
    const tester = new PEContainersTester();
    
    console.log('🔍 PE Containers Unit Tests');
    console.log('============================\n');

    // ==========================================
    // SECTION 1: Dockerfile Validation
    // ==========================================
    console.log('\n--- Section 1: Dockerfile Validation ---');

    await tester.test('Dockerfile.pe-vmkit exists', async () => {
        const exists = await tester.fileExists(join(dockerfilesDir, 'Dockerfile.pe-vmkit'));
        if (!exists) {
            throw new Error('Dockerfile.pe-vmkit not found');
        }
    });

    await tester.test('Dockerfile.pe-reactos exists', async () => {
        const exists = await tester.fileExists(join(dockerfilesDir, 'Dockerfile.pe-reactos'));
        if (!exists) {
            throw new Error('Dockerfile.pe-reactos not found');
        }
    });

    await tester.test('Dockerfile.macos-qemu exists', async () => {
        const exists = await tester.fileExists(join(dockerfilesDir, 'Dockerfile.macos-qemu'));
        if (!exists) {
            throw new Error('Dockerfile.macos-qemu not found');
        }
    });

    await tester.test('PE-VMKit Dockerfile has QEMU installation', async () => {
        const content = await tester.readFile(join(dockerfilesDir, 'Dockerfile.pe-vmkit'));
        if (!content.includes('qemu-system-x86')) {
            throw new Error('Dockerfile.pe-vmkit missing QEMU installation');
        }
    });

    await tester.test('PE-VMKit Dockerfile has VMKit scripts', async () => {
        const content = await tester.readFile(join(dockerfilesDir, 'Dockerfile.pe-vmkit'));
        if (!content.includes('vmkit-run.sh') || !content.includes('vmkit-create.sh')) {
            throw new Error('Dockerfile.pe-vmkit missing VMKit scripts');
        }
    });

    await tester.test('PE-ReactOS Dockerfile has setup script', async () => {
        const content = await tester.readFile(join(dockerfilesDir, 'Dockerfile.pe-reactos'));
        if (!content.includes('setup-reactos.sh') || !content.includes('run-pe.sh')) {
            throw new Error('Dockerfile.pe-reactos missing setup or run scripts');
        }
    });

    await tester.test('macOS-QEMU Dockerfile has proper labels', async () => {
        const content = await tester.readFile(join(dockerfilesDir, 'Dockerfile.macos-qemu'));
        if (!content.includes('os.type="macos-qemu"')) {
            throw new Error('Dockerfile.macos-qemu missing proper labels');
        }
    });

    await tester.test('macOS-QEMU Dockerfile has run-macos script', async () => {
        const content = await tester.readFile(join(dockerfilesDir, 'Dockerfile.macos-qemu'));
        if (!content.includes('run-macos.sh')) {
            throw new Error('Dockerfile.macos-qemu missing run-macos script');
        }
    });

    // ==========================================
    // SECTION 2: Pfyfile.pe-containers.pf Validation
    // ==========================================
    console.log('\n--- Section 2: Pfyfile.pe-containers.pf Validation ---');

    await tester.test('Pfyfile.pe-containers.pf exists', async () => {
        const exists = await tester.fileExists(join(projectRoot, 'Pfyfile.pe-containers.pf'));
        if (!exists) {
            throw new Error('Pfyfile.pe-containers.pf not found');
        }
    });

    await tester.test('Pfyfile has pe-build-all task', async () => {
        const content = await tester.readFile(join(projectRoot, 'Pfyfile.pe-containers.pf'));
        if (!content.includes('task pe-build-all')) {
            throw new Error('pe-build-all task not found');
        }
    });

    await tester.test('Pfyfile has pe-vmkit-run task', async () => {
        const content = await tester.readFile(join(projectRoot, 'Pfyfile.pe-containers.pf'));
        if (!content.includes('task pe-vmkit-run')) {
            throw new Error('pe-vmkit-run task not found');
        }
    });

    await tester.test('Pfyfile has pe-reactos-run task', async () => {
        const content = await tester.readFile(join(projectRoot, 'Pfyfile.pe-containers.pf'));
        if (!content.includes('task pe-reactos-run')) {
            throw new Error('pe-reactos-run task not found');
        }
    });

    await tester.test('Pfyfile has macos-run task', async () => {
        const content = await tester.readFile(join(projectRoot, 'Pfyfile.pe-containers.pf'));
        if (!content.includes('task macos-run')) {
            throw new Error('macos-run task not found');
        }
    });

    await tester.test('Pfyfile has pe-help task', async () => {
        const content = await tester.readFile(join(projectRoot, 'Pfyfile.pe-containers.pf'));
        if (!content.includes('task pe-help')) {
            throw new Error('pe-help task not found');
        }
    });

    // ==========================================
    // SECTION 3: Build Script Validation
    // ==========================================
    console.log('\n--- Section 3: Build Script Validation ---');

    await tester.test('build-containers.sh supports pe target', async () => {
        const content = await tester.readFile(join(projectRoot, 'containers/scripts/build-containers.sh'));
        if (!content.includes('build_pe_containers')) {
            throw new Error('build-containers.sh missing build_pe_containers function');
        }
        if (!content.includes('pe)')) {
            throw new Error('build-containers.sh missing pe target case');
        }
    });

    await tester.test('build-containers.sh builds pe-vmkit', async () => {
        const content = await tester.readFile(join(projectRoot, 'containers/scripts/build-containers.sh'));
        if (!content.includes('"pe-vmkit"') || !content.includes('Dockerfile.pe-vmkit')) {
            throw new Error('build-containers.sh missing pe-vmkit build');
        }
    });

    await tester.test('build-containers.sh builds pe-reactos', async () => {
        const content = await tester.readFile(join(projectRoot, 'containers/scripts/build-containers.sh'));
        if (!content.includes('"pe-reactos"') || !content.includes('Dockerfile.pe-reactos')) {
            throw new Error('build-containers.sh missing pe-reactos build');
        }
    });

    await tester.test('build-containers.sh builds macos-qemu', async () => {
        const content = await tester.readFile(join(projectRoot, 'containers/scripts/build-containers.sh'));
        if (!content.includes('"macos-qemu"') || !content.includes('Dockerfile.macos-qemu')) {
            throw new Error('build-containers.sh missing macos-qemu build');
        }
    });

    // ==========================================
    // SECTION 4: pf Syntax Integration
    // ==========================================
    console.log('\n--- Section 4: pf Syntax Integration ---');

    await tester.testSyntaxValid('Basic pe-build task', `
task pe-build
  describe Build PE container
  shell podman build -t localhost/pf-pe-vmkit:latest -f containers/dockerfiles/Dockerfile.pe-vmkit .
end
`);

    await tester.testSyntaxValid('PE run task with parameter', `
task pe-run pe=""
  describe Run PE file
  shell_lang bash
  shell echo "Running PE: \${pe}"
end
`);

    await tester.testSyntaxValid('macOS setup task', `
task macos-setup
  describe Set up macOS environment
  shell_lang bash
  shell mkdir -p macos-images
end
`);

    await tester.testSyntaxValid('PE analyze and run workflow', `
task pe-analyze-run pe=""
  describe Analyze and run PE
  shell pf pe-analyze pe=\${pe}
  shell pf pe-run pe=\${pe}
end
`);

    await tester.testSyntaxValid('Combined PE setup task', `
task pe-setup-all
  describe Set up all PE environments
  shell_lang bash
  shell |
    echo "Setting up PE environments..."
    pf pe-build-all
    pf pe-vmkit-setup
    pf pe-reactos-setup
end
`);

    // ==========================================
    // SECTION 5: Dockerfile Content Quality
    // ==========================================
    console.log('\n--- Section 5: Dockerfile Content Quality ---');

    await tester.test('PE-VMKit has proper FROM directive', async () => {
        const content = await tester.readFile(join(dockerfilesDir, 'Dockerfile.pe-vmkit'));
        if (!content.includes('FROM ubuntu:22.04')) {
            throw new Error('Dockerfile.pe-vmkit should use ubuntu:22.04 base');
        }
    });

    await tester.test('PE-VMKit has proper WORKDIR', async () => {
        const content = await tester.readFile(join(dockerfilesDir, 'Dockerfile.pe-vmkit'));
        if (!content.includes('WORKDIR /vmkit')) {
            throw new Error('Dockerfile.pe-vmkit missing WORKDIR');
        }
    });

    await tester.test('PE-ReactOS has proper environment variables', async () => {
        const content = await tester.readFile(join(dockerfilesDir, 'Dockerfile.pe-reactos'));
        if (!content.includes('ENV OS_TYPE=pe-reactos')) {
            throw new Error('Dockerfile.pe-reactos missing OS_TYPE env');
        }
    });

    await tester.test('macOS-QEMU has exposed ports', async () => {
        const content = await tester.readFile(join(dockerfilesDir, 'Dockerfile.macos-qemu'));
        if (!content.includes('EXPOSE 5901') || !content.includes('10022')) {
            throw new Error('Dockerfile.macos-qemu missing EXPOSE ports');
        }
    });

    await tester.test('Dockerfiles have VOLUME declarations', async () => {
        const vmkitContent = await tester.readFile(join(dockerfilesDir, 'Dockerfile.pe-vmkit'));
        const reactosContent = await tester.readFile(join(dockerfilesDir, 'Dockerfile.pe-reactos'));
        const macosContent = await tester.readFile(join(dockerfilesDir, 'Dockerfile.macos-qemu'));
        
        if (!vmkitContent.includes('VOLUME')) {
            throw new Error('Dockerfile.pe-vmkit missing VOLUME');
        }
        if (!reactosContent.includes('VOLUME')) {
            throw new Error('Dockerfile.pe-reactos missing VOLUME');
        }
        if (!macosContent.includes('VOLUME')) {
            throw new Error('Dockerfile.macos-qemu missing VOLUME');
        }
    });

    // ==========================================
    // SECTION 6: Script Content Validation
    // ==========================================
    console.log('\n--- Section 6: Script Content Validation ---');

    await tester.test('VMKit scripts handle KVM detection', async () => {
        const content = await tester.readFile(join(dockerfilesDir, 'Dockerfile.pe-vmkit'));
        if (!content.includes('/dev/kvm')) {
            throw new Error('VMKit scripts should handle KVM detection');
        }
    });

    await tester.test('ReactOS scripts have PE validation', async () => {
        const content = await tester.readFile(join(dockerfilesDir, 'Dockerfile.pe-reactos'));
        if (!content.includes('PE32') || !content.includes('file -b')) {
            throw new Error('ReactOS scripts should validate PE files');
        }
    });

    await tester.test('macOS scripts have legal notice', async () => {
        const content = await tester.readFile(join(dockerfilesDir, 'Dockerfile.macos-qemu'));
        if (!content.includes('legal') || !content.includes('license')) {
            throw new Error('macOS container should include legal notice');
        }
    });

    // Print summary
    console.log('\n============================');
    console.log('📊 PE Containers Test Results');
    console.log('============================');
    console.log(`✅ Passed: ${tester.passed}`);
    console.log(`❌ Failed: ${tester.failed}`);
    console.log(`📈 Success Rate: ${Math.round((tester.passed / (tester.passed + tester.failed)) * 100)}%`);

    if (tester.failed === 0) {
        console.log('\n🎉 All PE container tests passed!');
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

export { runTests, PEContainersTester };
