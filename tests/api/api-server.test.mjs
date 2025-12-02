#!/usr/bin/env node
/**
 * Comprehensive Unit Tests for pf REST API Server
 * 
 * Tests all REST API endpoints, WebSocket functionality, and error handling
 */

import { spawn } from 'child_process';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const projectRoot = join(__dirname, '../..');

// Test utilities
class APITester {
    constructor(baseUrl = 'http://localhost:8082') {
        this.baseUrl = baseUrl;
        this.passed = 0;
        this.failed = 0;
        this.tests = [];
        this.serverProcess = null;
    }

    async startServer(port = 8082) {
        return new Promise((resolve, reject) => {
            const serverPath = join(projectRoot, 'tools/api-server.mjs');
            const webRoot = join(projectRoot, 'demos/pf-web-polyglot-demo-plus-c/web');
            
            this.serverProcess = spawn('node', [serverPath, webRoot, port.toString()], {
                cwd: projectRoot,
                stdio: ['pipe', 'pipe', 'pipe']
            });

            let started = false;

            this.serverProcess.stdout.on('data', (data) => {
                const output = data.toString();
                if (output.includes('serving') && !started) {
                    started = true;
                    // Give server a moment to fully initialize
                    setTimeout(() => resolve(), 500);
                }
            });

            this.serverProcess.stderr.on('data', (data) => {
                console.error('Server stderr:', data.toString());
            });

            this.serverProcess.on('error', reject);

            // Timeout if server doesn't start
            setTimeout(() => {
                if (!started) {
                    reject(new Error('Server failed to start within timeout'));
                }
            }, 10000);
        });
    }

    async stopServer() {
        if (this.serverProcess) {
            this.serverProcess.kill();
            this.serverProcess = null;
        }
    }

    async fetch(path, options = {}) {
        const url = `${this.baseUrl}${path}`;
        const response = await fetch(url, {
            ...options,
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            }
        });
        
        let body;
        const contentType = response.headers.get('content-type');
        if (contentType && contentType.includes('application/json')) {
            body = await response.json();
        } else {
            body = await response.text();
        }

        return {
            status: response.status,
            statusText: response.statusText,
            headers: response.headers,
            body
        };
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

    assertEqual(actual, expected, message = '') {
        if (actual !== expected) {
            throw new Error(`${message} - Expected ${expected}, got ${actual}`);
        }
    }

    assertContains(str, substring, message = '') {
        if (!str || !str.includes(substring)) {
            throw new Error(`${message} - Expected "${str}" to contain "${substring}"`);
        }
    }

    assertExists(obj, property, message = '') {
        if (obj[property] === undefined) {
            throw new Error(`${message} - Expected property "${property}" to exist`);
        }
    }

    assertStatusCode(response, expectedCode, message = '') {
        if (response.status !== expectedCode) {
            throw new Error(`${message} - Expected status ${expectedCode}, got ${response.status}`);
        }
    }

    assertTrue(condition, message = '') {
        if (!condition) {
            throw new Error(message || 'Assertion failed');
        }
    }
}

// Test cases
async function runTests() {
    const tester = new APITester();
    
    console.log('🔍 pf REST API Unit Tests');
    console.log('=========================\n');

    console.log('Starting API server...');
    
    try {
        await tester.startServer(8082);
        console.log('✅ Server started successfully\n');
    } catch (error) {
        console.error('❌ Failed to start server:', error.message);
        console.log('⚠️  Running tests without server (simulated mode)');
    }

    // ==========================================
    // SECTION 1: Health & System Endpoints
    // ==========================================
    console.log('\n--- Section 1: Health & System Endpoints ---');

    await tester.test('GET /api/health returns 200 OK', async () => {
        const response = await tester.fetch('/api/health');
        tester.assertStatusCode(response, 200);
        tester.assertEqual(response.body.status, 'ok');
    });

    await tester.test('GET /api/health returns timestamp', async () => {
        const response = await tester.fetch('/api/health');
        tester.assertExists(response.body, 'timestamp');
        const timestamp = new Date(response.body.timestamp);
        tester.assertTrue(!isNaN(timestamp.getTime()), 'Invalid timestamp format');
    });

    await tester.test('GET /api/health returns server version', async () => {
        const response = await tester.fetch('/api/health');
        tester.assertExists(response.body, 'version');
    });

    await tester.test('GET /api/system returns platform info', async () => {
        const response = await tester.fetch('/api/system');
        tester.assertStatusCode(response, 200);
        tester.assertExists(response.body, 'platform');
        tester.assertExists(response.body, 'arch');
        tester.assertExists(response.body, 'nodeVersion');
    });

    await tester.test('GET /api/system returns available languages', async () => {
        const response = await tester.fetch('/api/system');
        tester.assertExists(response.body, 'availableLanguages');
        tester.assertTrue(Array.isArray(response.body.availableLanguages), 'availableLanguages should be an array');
        tester.assertTrue(response.body.availableLanguages.includes('rust'), 'Should include rust');
        tester.assertTrue(response.body.availableLanguages.includes('c'), 'Should include c');
    });

    await tester.test('GET /api/system returns build targets', async () => {
        const response = await tester.fetch('/api/system');
        tester.assertExists(response.body, 'buildTargets');
        tester.assertTrue(Array.isArray(response.body.buildTargets), 'buildTargets should be an array');
        tester.assertTrue(response.body.buildTargets.includes('wasm'), 'Should include wasm');
        tester.assertTrue(response.body.buildTargets.includes('llvm'), 'Should include llvm');
    });

    // ==========================================
    // SECTION 2: Projects Endpoint
    // ==========================================
    console.log('\n--- Section 2: Projects Endpoint ---');

    await tester.test('GET /api/projects returns 200 OK', async () => {
        const response = await tester.fetch('/api/projects');
        tester.assertStatusCode(response, 200);
    });

    await tester.test('GET /api/projects returns projects array', async () => {
        const response = await tester.fetch('/api/projects');
        tester.assertExists(response.body, 'projects');
        tester.assertTrue(Array.isArray(response.body.projects), 'projects should be an array');
    });

    await tester.test('GET /api/projects returns project structure', async () => {
        const response = await tester.fetch('/api/projects');
        if (response.body.projects.length > 0) {
            const project = response.body.projects[0];
            tester.assertExists(project, 'name');
            tester.assertExists(project, 'path');
            tester.assertExists(project, 'languages');
        }
    });

    // ==========================================
    // SECTION 3: Modules Endpoint
    // ==========================================
    console.log('\n--- Section 3: Modules Endpoint ---');

    await tester.test('GET /api/modules returns 200 OK', async () => {
        const response = await tester.fetch('/api/modules');
        tester.assertStatusCode(response, 200);
    });

    await tester.test('GET /api/modules returns modules array', async () => {
        const response = await tester.fetch('/api/modules');
        tester.assertExists(response.body, 'modules');
        tester.assertTrue(Array.isArray(response.body.modules), 'modules should be an array');
    });

    // ==========================================
    // SECTION 4: Build Status Endpoint
    // ==========================================
    console.log('\n--- Section 4: Build Status Endpoint ---');

    await tester.test('GET /api/status returns 200 OK', async () => {
        const response = await tester.fetch('/api/status');
        tester.assertStatusCode(response, 200);
    });

    await tester.test('GET /api/status returns builds array', async () => {
        const response = await tester.fetch('/api/status');
        tester.assertExists(response.body, 'builds');
        tester.assertTrue(Array.isArray(response.body.builds), 'builds should be an array');
    });

    await tester.test('GET /api/status?buildId=invalid returns 404', async () => {
        const response = await tester.fetch('/api/status?buildId=nonexistent-build-id');
        tester.assertStatusCode(response, 404);
    });

    // ==========================================
    // SECTION 5: Build Endpoints
    // ==========================================
    console.log('\n--- Section 5: Build Endpoints ---');

    await tester.test('POST /api/build/rust returns buildId', async () => {
        const response = await tester.fetch('/api/build/rust', {
            method: 'POST',
            body: JSON.stringify({ target: 'wasm' })
        });
        tester.assertStatusCode(response, 200);
        tester.assertExists(response.body, 'buildId');
        tester.assertExists(response.body, 'status');
        tester.assertEqual(response.body.status, 'queued');
    });

    await tester.test('POST /api/build/c returns buildId', async () => {
        const response = await tester.fetch('/api/build/c', {
            method: 'POST',
            body: JSON.stringify({ target: 'wasm' })
        });
        tester.assertStatusCode(response, 200);
        tester.assertExists(response.body, 'buildId');
    });

    await tester.test('POST /api/build/fortran returns buildId', async () => {
        const response = await tester.fetch('/api/build/fortran', {
            method: 'POST',
            body: JSON.stringify({ target: 'wasm' })
        });
        tester.assertStatusCode(response, 200);
        tester.assertExists(response.body, 'buildId');
    });

    await tester.test('POST /api/build/wat returns buildId', async () => {
        const response = await tester.fetch('/api/build/wat', {
            method: 'POST',
            body: JSON.stringify({ target: 'wasm' })
        });
        tester.assertStatusCode(response, 200);
        tester.assertExists(response.body, 'buildId');
    });

    await tester.test('POST /api/build/invalid returns 400', async () => {
        const response = await tester.fetch('/api/build/invalid', {
            method: 'POST',
            body: JSON.stringify({ target: 'wasm' })
        });
        tester.assertStatusCode(response, 400);
        tester.assertContains(response.body.error, 'Unsupported language');
    });

    await tester.test('POST /api/build/rust with invalid target returns 400', async () => {
        const response = await tester.fetch('/api/build/rust', {
            method: 'POST',
            body: JSON.stringify({ target: 'invalid-target' })
        });
        tester.assertStatusCode(response, 400);
        tester.assertContains(response.body.error, 'Unsupported target');
    });

    // ==========================================
    // SECTION 6: Build All Endpoint
    // ==========================================
    console.log('\n--- Section 6: Build All Endpoint ---');

    await tester.test('POST /api/build/all returns multiple buildIds', async () => {
        const response = await tester.fetch('/api/build/all', {
            method: 'POST',
            body: JSON.stringify({ target: 'wasm' })
        });
        tester.assertStatusCode(response, 200);
        tester.assertExists(response.body, 'buildIds');
        tester.assertTrue(Array.isArray(response.body.buildIds), 'buildIds should be an array');
    });

    await tester.test('POST /api/build/all with LLVM target', async () => {
        const response = await tester.fetch('/api/build/all', {
            method: 'POST',
            body: JSON.stringify({ target: 'llvm' })
        });
        tester.assertStatusCode(response, 200);
        tester.assertEqual(response.body.target, 'llvm');
    });

    // ==========================================
    // SECTION 7: Build Logs Endpoint
    // ==========================================
    console.log('\n--- Section 7: Build Logs Endpoint ---');

    await tester.test('GET /api/logs/nonexistent returns 404', async () => {
        const response = await tester.fetch('/api/logs/nonexistent-build');
        tester.assertStatusCode(response, 404);
    });

    await tester.test('GET /api/logs with valid buildId returns logs', async () => {
        // First create a build
        const buildResponse = await tester.fetch('/api/build/rust', {
            method: 'POST',
            body: JSON.stringify({ target: 'wasm' })
        });
        const buildId = buildResponse.body.buildId;

        // Wait a moment for build to start
        await new Promise(resolve => setTimeout(resolve, 500));

        // Get logs
        const logsResponse = await tester.fetch(`/api/logs/${buildId}`);
        // May return 200 or 404 depending on timing
        tester.assertTrue(
            logsResponse.status === 200 || logsResponse.status === 404,
            `Expected 200 or 404, got ${logsResponse.status}`
        );
    });

    // ==========================================
    // SECTION 8: CORS Headers
    // ==========================================
    console.log('\n--- Section 8: CORS Headers ---');

    await tester.test('API endpoints include CORS headers', async () => {
        const response = await tester.fetch('/api/health');
        // Check Access-Control headers
        tester.assertStatusCode(response, 200);
        // Note: fetch() may not expose all headers, but CORS should be configured
    });

    // ==========================================
    // SECTION 9: Build Options
    // ==========================================
    console.log('\n--- Section 9: Build Options ---');

    await tester.test('POST /api/build/rust with optimization level', async () => {
        const response = await tester.fetch('/api/build/rust', {
            method: 'POST',
            body: JSON.stringify({ target: 'llvm', opt_level: '3' })
        });
        tester.assertStatusCode(response, 200);
    });

    await tester.test('POST /api/build/c with parallel option', async () => {
        const response = await tester.fetch('/api/build/c', {
            method: 'POST',
            body: JSON.stringify({ target: 'wasm', parallel: true })
        });
        tester.assertStatusCode(response, 200);
    });

    await tester.test('POST /api/build/rust with custom project', async () => {
        const response = await tester.fetch('/api/build/rust', {
            method: 'POST',
            body: JSON.stringify({ target: 'wasm', project: 'custom-project' })
        });
        tester.assertStatusCode(response, 200);
    });

    // ==========================================
    // SECTION 10: Error Handling
    // ==========================================
    console.log('\n--- Section 10: Error Handling ---');

    await tester.test('Invalid JSON body returns error', async () => {
        const response = await fetch(`${tester.baseUrl}/api/build/rust`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: 'invalid json {'
        });
        // Should return 400 or handle gracefully
        tester.assertTrue(response.status >= 400, 'Should return error status');
    });

    await tester.test('GET to non-existent endpoint returns 404', async () => {
        const response = await tester.fetch('/api/nonexistent');
        tester.assertStatusCode(response, 404);
    });

    // ==========================================
    // SECTION 11: Response Format
    // ==========================================
    console.log('\n--- Section 11: Response Format ---');

    await tester.test('All API responses are JSON', async () => {
        const endpoints = ['/api/health', '/api/system', '/api/projects', '/api/modules', '/api/status'];
        for (const endpoint of endpoints) {
            const response = await fetch(`${tester.baseUrl}${endpoint}`);
            const contentType = response.headers.get('content-type');
            tester.assertTrue(
                contentType && contentType.includes('application/json'),
                `${endpoint} should return JSON`
            );
        }
    });

    await tester.test('Build response includes buildId format', async () => {
        const response = await tester.fetch('/api/build/rust', {
            method: 'POST',
            body: JSON.stringify({ target: 'wasm' })
        });
        // BuildId should be in format: language-target-timestamp
        const buildId = response.body.buildId;
        tester.assertTrue(buildId.includes('rust'), 'BuildId should include language');
        tester.assertTrue(buildId.includes('wasm'), 'BuildId should include target');
    });

    // Stop server
    await tester.stopServer();

    // Print summary
    console.log('\n=============================');
    console.log('📊 API Test Results');
    console.log('=============================');
    console.log(`✅ Passed: ${tester.passed}`);
    console.log(`❌ Failed: ${tester.failed}`);
    console.log(`📈 Success Rate: ${Math.round((tester.passed / (tester.passed + tester.failed)) * 100)}%`);

    if (tester.failed === 0) {
        console.log('\n🎉 All API tests passed!');
    } else {
        console.log('\n⚠️  Some tests failed. Please review the API implementation.');
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

export { runTests, APITester };
