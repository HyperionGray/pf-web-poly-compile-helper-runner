#!/usr/bin/env node

import { promises as fs } from 'fs';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const projectRoot = join(__dirname, '../..');

class VmkitImagesReviewTester {
    constructor() {
        this.passed = 0;
        this.failed = 0;
    }

    async test(name, fn) {
        try {
            console.log(`\n🧪 Testing: ${name}`);
            await fn();
            console.log(`✅ PASS: ${name}`);
            this.passed++;
        } catch (error) {
            console.log(`❌ FAIL: ${name}`);
            console.log(`   Error: ${error.message}`);
            this.failed++;
        }
    }
}

async function runTests() {
    const tester = new VmkitImagesReviewTester();
    const vmkitImagesDir = join(projectRoot, 'vmkit-images');

    console.log('🔍 VMKit Images Review Tests');
    console.log('============================\n');

    await tester.test('vmkit-images directory exists', async () => {
        const stat = await fs.stat(vmkitImagesDir);
        if (!stat.isDirectory()) {
            throw new Error('vmkit-images path is not a directory');
        }
    });

    await tester.test('required VMKit qcow2 images exist', async () => {
        await fs.access(join(vmkitImagesDir, 'reactos.qcow2'));
        await fs.access(join(vmkitImagesDir, 'minimal.qcow2'));
    });

    await tester.test('ReactOS ISO is present or explicitly marked removed', async () => {
        const isoPath = join(vmkitImagesDir, 'reactos-livecd.iso');
        const markerPath = join(vmkitImagesDir, 'reactos-livecd.iso.REMOVED.git-id');

        try {
            await fs.access(isoPath);
            return;
        } catch {
            const marker = (await fs.readFile(markerPath, 'utf-8')).trim();
            if (!/^[0-9a-f]{40}$/i.test(marker)) {
                throw new Error('ISO removal marker is missing a valid git id');
            }
        }
    });

    await tester.test('VMKit helper scripts are executable for pf task execution', async () => {
        const runStat = await fs.stat(join(projectRoot, 'scripts/pe/vmkit-run.sh'));
        const analyzeStat = await fs.stat(join(projectRoot, 'scripts/pe/vmkit-analyze.sh'));

        if ((runStat.mode & 0o111) === 0) {
            throw new Error('scripts/pe/vmkit-run.sh is not executable');
        }
        if ((analyzeStat.mode & 0o111) === 0) {
            throw new Error('scripts/pe/vmkit-analyze.sh is not executable');
        }
    });

    console.log('\n============================');
    console.log('📊 VMKit Images Review Results');
    console.log('============================');
    console.log(`✅ Passed: ${tester.passed}`);
    console.log(`❌ Failed: ${tester.failed}`);

    return tester.failed === 0;
}

if (import.meta.url === `file://${process.argv[1]}`) {
    runTests().then(success => process.exit(success ? 0 : 1)).catch(error => {
        console.error('Test runner error:', error);
        process.exit(1);
    });
}

export { runTests };
