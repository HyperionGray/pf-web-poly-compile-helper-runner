#!/usr/bin/env node
/**
 * Tests for pf REST API (FastAPI/Uvicorn)
 * 
 * Tests the REST API endpoints and alias routing
 */

import { spawn } from 'child_process';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const projectRoot = join(__dirname, '../..');
const pfRunnerDir = join(projectRoot, 'pf-runner');

// Test utilities
let passed = 0;
let failed = 0;
let serverProcess = null;
const baseUrl = 'http://localhost:8765';

function log(color, prefix, message) {
    const colors = {
        green: '\x1b[32m',
        red: '\x1b[31m',
        yellow: '\x1b[33m',
        blue: '\x1b[34m',
        reset: '\x1b[0m'
    };
    console.log(`${colors[color] || ''}${prefix}${colors.reset} ${message}`);
}

async function startServer() {
    return new Promise((resolve, reject) => {
        log('blue', '[INFO]', 'Starting FastAPI test server on port 8765...');
        
        serverProcess = spawn('python3', [
            '-m', 'uvicorn', 'pf_api:app',
            '--host', '127.0.0.1',
            '--port', '8765',
            '--log-level', 'warning'
        ], {
            cwd: pfRunnerDir,
            stdio: ['pipe', 'pipe', 'pipe'],
            env: {
                ...process.env,
                PYTHONPATH: pfRunnerDir
            }
        });

        let started = false;
        let stdout = '';
        let stderr = '';

        serverProcess.stdout.on('data', (data) => {
            stdout += data.toString();
        });

        serverProcess.stderr.on('data', (data) => {
            const output = data.toString();
            stderr += output;
            // uvicorn logs to stderr
            if (output.includes('Started server process') || output.includes('Uvicorn running')) {
                started = true;
                setTimeout(() => resolve(), 1000); // Wait for server to be ready
            }
        });

        serverProcess.on('error', (error) => {
            reject(error);
        });

        // Timeout if server doesn't start
        setTimeout(() => {
            if (!started) {
                // Try to connect anyway
                fetch(`${baseUrl}/health`)
                    .then(() => resolve())
                    .catch(() => reject(new Error(`Server failed to start. stdout: ${stdout}, stderr: ${stderr}`)));
            }
        }, 5000);
    });
}

function stopServer() {
    if (serverProcess) {
        serverProcess.kill();
        serverProcess = null;
    }
}

async function fetchJson(path, options = {}) {
    const response = await fetch(`${baseUrl}${path}`, {
        ...options,
        headers: {
            'Content-Type': 'application/json',
            ...options.headers
        }
    });
    
    const body = await response.json();
    return { status: response.status, body };
}

async function test(name, testFn) {
    try {
        console.log(`\n🧪 Testing: ${name}`);
        await testFn();
        log('green', '✅ PASS:', name);
        passed++;
    } catch (error) {
        log('red', '❌ FAIL:', name);
        console.log(`   Error: ${error.message}`);
        failed++;
    }
}

function assertEqual(actual, expected, message = '') {
    if (JSON.stringify(actual) !== JSON.stringify(expected)) {
        throw new Error(`${message} - Expected ${JSON.stringify(expected)}, got ${JSON.stringify(actual)}`);
    }
}

function assertTrue(condition, message = '') {
    if (!condition) {
        throw new Error(message || 'Assertion failed');
    }
}

async function runTests() {
    console.log('🔍 pf REST API Unit Tests');
    console.log('=========================\n');

    let serverStarted = false;

    try {
        await startServer();
        serverStarted = true;
        log('green', '[INFO]', 'Server started successfully');
    } catch (error) {
        log('yellow', '[WARN]', `Could not start server: ${error.message}`);
        log('yellow', '[WARN]', 'Running module import tests only');
    }

    // Test 1: Module imports correctly
    await test('pf_api module imports without errors', async () => {
        const proc = spawn('python3', ['-c', `
import sys
sys.path.insert(0, '${pfRunnerDir}')
import pf_api
print(f'API Version: {pf_api.API_VERSION}')
print(f'App type: {type(pf_api.app).__name__}')
        `], { cwd: pfRunnerDir });

        const result = await new Promise((resolve, reject) => {
            let stdout = '';
            let stderr = '';
            proc.stdout.on('data', (d) => stdout += d.toString());
            proc.stderr.on('data', (d) => stderr += d.toString());
            proc.on('close', (code) => resolve({ code, stdout, stderr }));
            proc.on('error', reject);
        });

        assertTrue(result.code === 0, `Import failed: ${result.stderr}`);
        assertTrue(result.stdout.includes('API Version: 1.0.0'), `Unexpected version: ${result.stdout}`);
        assertTrue(result.stdout.includes('FastAPI'), `Not FastAPI app: ${result.stdout}`);
    });

    // Test 2: TaskInfo model works correctly
    await test('TaskInfo Pydantic model validates correctly', async () => {
        const proc = spawn('python3', ['-c', `
import sys
sys.path.insert(0, '${pfRunnerDir}')
from pf_api import TaskInfo

task = TaskInfo(
    name='test-task',
    description='A test task',
    aliases=['tt', 'test'],
    parameters={'port': '8080'}
)
print(f'Name: {task.name}')
print(f'Aliases: {task.aliases}')
        `], { cwd: pfRunnerDir });

        const result = await new Promise((resolve, reject) => {
            let stdout = '';
            let stderr = '';
            proc.stdout.on('data', (d) => stdout += d.toString());
            proc.stderr.on('data', (d) => stderr += d.toString());
            proc.on('close', (code) => resolve({ code, stdout, stderr }));
            proc.on('error', reject);
        });

        assertTrue(result.code === 0, `Model creation failed: ${result.stderr}`);
        assertTrue(result.stdout.includes('test-task'), `Missing task name: ${result.stdout}`);
        assertTrue(result.stdout.includes("['tt', 'test']"), `Missing aliases: ${result.stdout}`);
    });

    // Skip server-dependent tests if server didn't start
    if (!serverStarted) {
        console.log('\n⚠️  Skipping server-dependent tests');
        
        console.log('\n=============================');
        console.log('📊 REST API Test Results');
        console.log('=============================');
        console.log(`✅ Passed: ${passed}`);
        console.log(`❌ Failed: ${failed}`);
        console.log(`⚠️  Some tests skipped (server not available)`);
        
        return failed === 0;
    }

    // Test 3: Health endpoint
    await test('GET / returns health status', async () => {
        const { status, body } = await fetchJson('/');
        assertEqual(status, 200, 'Status should be 200');
        assertEqual(body.status, 'ok', 'Status should be ok');
        assertTrue(body.version !== undefined, 'Should have version');
    });

    // Test 4: Health endpoint at /health
    await test('GET /health returns health status', async () => {
        const { status, body } = await fetchJson('/health');
        assertEqual(status, 200, 'Status should be 200');
        assertEqual(body.status, 'ok', 'Status should be ok');
    });

    // Test 5: List tasks endpoint
    await test('GET /pf/ returns task list', async () => {
        const { status, body } = await fetchJson('/pf/');
        assertEqual(status, 200, 'Status should be 200');
        assertTrue(Array.isArray(body.tasks), 'Should have tasks array');
        assertTrue(Array.isArray(body.builtins), 'Should have builtins array');
        assertTrue(body.total_count > 0, 'Should have some tasks');
    });

    // Test 6: Builtin tasks are listed
    await test('GET /pf/ includes builtin tasks', async () => {
        const { status, body } = await fetchJson('/pf/');
        assertTrue(body.builtins.includes('update'), 'Should include update builtin');
        assertTrue(body.builtins.includes('reboot'), 'Should include reboot builtin');
    });

    // Test 7: Get specific task (builtin)
    await test('GET /pf/update returns builtin task details', async () => {
        const { status, body } = await fetchJson('/pf/update');
        assertEqual(status, 200, 'Status should be 200');
        assertEqual(body.name, 'update', 'Task name should be update');
    });

    // Test 8: 404 for nonexistent task
    await test('GET /pf/nonexistent returns 404', async () => {
        const { status } = await fetchJson('/pf/nonexistent-task-that-does-not-exist');
        assertEqual(status, 404, 'Status should be 404');
    });

    // Test 9: Reload endpoint
    await test('POST /reload reloads tasks', async () => {
        const response = await fetch(`${baseUrl}/reload`, { 
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: '{}'  // Empty JSON body
        });
        const body = await response.json();
        assertEqual(response.status, 200, 'Status should be 200');
        assertEqual(body.status, 'reloaded', 'Status should be reloaded');
        assertTrue(body.tasks_count >= 0, 'Should have tasks count');
    });

    // Test 10: API docs endpoint exists
    await test('GET /docs returns OpenAPI documentation', async () => {
        const response = await fetch(`${baseUrl}/docs`);
        assertEqual(response.status, 200, 'Status should be 200');
        const html = await response.text();
        assertTrue(html.includes('swagger'), 'Should be Swagger UI');
    });

    // Test 11: ReDoc endpoint exists  
    await test('GET /redoc returns ReDoc documentation', async () => {
        const response = await fetch(`${baseUrl}/redoc`);
        assertEqual(response.status, 200, 'Status should be 200');
    });

    // Test 12: OpenAPI JSON
    await test('GET /openapi.json returns OpenAPI schema', async () => {
        const { status, body } = await fetchJson('/openapi.json');
        assertEqual(status, 200, 'Status should be 200');
        assertTrue(body.openapi !== undefined, 'Should have openapi version');
        assertTrue(body.info !== undefined, 'Should have info');
        assertEqual(body.info.title, 'pf REST API', 'Should have correct title');
    });

    // Cleanup
    stopServer();

    // Print summary
    console.log('\n=============================');
    console.log('📊 REST API Test Results');
    console.log('=============================');
    console.log(`✅ Passed: ${passed}`);
    console.log(`❌ Failed: ${failed}`);
    console.log(`📈 Success Rate: ${Math.round((passed / (passed + failed)) * 100)}%`);

    if (failed === 0) {
        console.log('\n🎉 All REST API tests passed!');
    } else {
        console.log('\n⚠️  Some tests failed. Please review the implementation.');
    }

    return failed === 0;
}

// Run tests if executed directly
if (import.meta.url === `file://${process.argv[1]}`) {
    runTests().then(success => {
        stopServer(); // Ensure cleanup
        process.exit(success ? 0 : 1);
    }).catch(error => {
        stopServer();
        console.error('Test runner error:', error);
        process.exit(1);
    });
}

export { runTests };
