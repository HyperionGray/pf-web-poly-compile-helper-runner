#!/usr/bin/env node
/**
 * Simple test script for the REST API server
 * This verifies that the API endpoints are working correctly
 */

import { spawn } from 'node:child_process';
import { setTimeout } from 'node:timers/promises';

// Fetch helper that works across Node versions:
// - Node 18: no global fetch
// - Node 22: global fetch exists but node:fetch may be absent
async function getFetch() {
  if (globalThis.fetch) return globalThis.fetch;
  try {
    const undici = await import('undici');
    return undici.fetch;
  } catch {
    const { default: fetch } = await import('node-fetch');
    return fetch;
  }
}

const API_BASE = 'http://localhost:8080/api';

// Simple fetch implementation for Node.js
async function testFetch(url, options = {}) {
  const fetch = await getFetch();
  return fetch(url, options);
}

async function testHealthEndpoint() {
  console.log('🏥 Testing health endpoint...');
  try {
    const response = await testFetch(`${API_BASE}/health`);
    const data = await response.json();
    
    if (response.ok && data.status === 'ok') {
      console.log('✅ Health endpoint working');
      return true;
    } else {
      console.log('❌ Health endpoint failed:', data);
      return false;
    }
  } catch (error) {
    console.log('❌ Health endpoint error:', error.message);
    return false;
  }
}

async function testSystemEndpoint() {
  console.log('💻 Testing system endpoint...');
  try {
    const response = await testFetch(`${API_BASE}/system`);
    const data = await response.json();
    
    if (response.ok && data.platform && data.availableLanguages) {
      console.log('✅ System endpoint working');
      console.log('   Available languages:', data.availableLanguages.join(', '));
      return true;
    } else {
      console.log('❌ System endpoint failed:', data);
      return false;
    }
  } catch (error) {
    console.log('❌ System endpoint error:', error.message);
    return false;
  }
}

async function testProjectsEndpoint() {
  console.log('📁 Testing projects endpoint...');
  try {
    const response = await testFetch(`${API_BASE}/projects`);
    const data = await response.json();
    
    if (response.ok && data.projects) {
      console.log('✅ Projects endpoint working');
      console.log(`   Found ${data.projects.length} projects`);
      return true;
    } else {
      console.log('❌ Projects endpoint failed:', data);
      return false;
    }
  } catch (error) {
    console.log('❌ Projects endpoint error:', error.message);
    return false;
  }
}

async function testBuildEndpoint() {
  console.log('🔨 Testing build endpoint...');
  try {
    const response = await testFetch(`${API_BASE}/build/rust`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ target: 'wasm' })
    });
    const data = await response.json();
    
    if (response.ok && data.buildId) {
      console.log('✅ Build endpoint working');
      console.log('   Build ID:', data.buildId);
      return data.buildId;
    } else {
      console.log('❌ Build endpoint failed:', data);
      return null;
    }
  } catch (error) {
    console.log('❌ Build endpoint error:', error.message);
    return null;
  }
}

async function testStatusEndpoint(buildId = null) {
  console.log('📊 Testing status endpoint...');
  try {
    const url = buildId ? `${API_BASE}/status?buildId=${buildId}` : `${API_BASE}/status`;
    const response = await testFetch(url);
    const data = await response.json();
    
    if (response.ok) {
      console.log('✅ Status endpoint working');
      if (buildId) {
        console.log('   Build status:', data.status);
      } else {
        console.log(`   Found ${data.builds?.length || 0} builds`);
      }
      return true;
    } else {
      console.log('❌ Status endpoint failed:', data);
      return false;
    }
  } catch (error) {
    console.log('❌ Status endpoint error:', error.message);
    return false;
  }
}

async function startApiServer() {
  console.log('🚀 Starting API server...');
  
  const server = spawn('node', ['tools/api-server.mjs', 'demos/pf-web-polyglot-demo-plus-c/web', '8080'], {
    stdio: ['pipe', 'pipe', 'pipe'],
    detached: false
  });
  
  // Wait for server to start
  await setTimeout(3000);
  
  return server;
}

async function runTests() {
  console.log('🧪 Starting REST API tests...\n');
  
  let server = null;
  
  try {
    // Start the API server
    server = await startApiServer();
    
    // Run tests
    const results = [];
    
    results.push(await testHealthEndpoint());
    results.push(await testSystemEndpoint());
    results.push(await testProjectsEndpoint());
    results.push(await testStatusEndpoint());
    
    const buildId = await testBuildEndpoint();
    if (buildId) {
      // Wait a bit for build to start
      await setTimeout(1000);
      results.push(await testStatusEndpoint(buildId));
    }
    
    // Summary
    const passed = results.filter(r => r === true).length;
    const total = results.length;
    
    console.log(`\n📋 Test Results: ${passed}/${total} passed`);
    
    if (passed === total) {
      console.log('🎉 All tests passed! REST API is working correctly.');
      process.exit(0);
    } else {
      console.log('⚠️  Some tests failed. Check the API server implementation.');
      process.exit(1);
    }
    
  } catch (error) {
    console.error('❌ Test error:', error.message);
    process.exit(1);
  } finally {
    if (server) {
      console.log('🛑 Stopping API server...');
      server.kill();
    }
  }
}

// Run tests if this file is executed directly
if (import.meta.url === `file://${process.argv[1]}`) {
  runTests().catch(console.error);
}

export { runTests };
