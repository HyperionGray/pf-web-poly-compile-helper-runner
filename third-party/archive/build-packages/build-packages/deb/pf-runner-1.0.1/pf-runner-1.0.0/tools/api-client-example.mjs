#!/usr/bin/env node
/**
 * Example API client for pf-web-poly-compile-helper-runner REST API
 * 
 * This demonstrates how to interact with the REST API endpoints
 * to trigger builds, check status, and retrieve logs.
 */

import fetch from 'node:fetch';
import WebSocket from 'ws';

const API_BASE = 'http://localhost:8080/api';
const WS_URL = 'ws://localhost:8080';

class PfApiClient {
  constructor(baseUrl = API_BASE) {
    this.baseUrl = baseUrl;
    this.ws = null;
  }

  // Connect to WebSocket for real-time updates
  connectWebSocket() {
    return new Promise((resolve, reject) => {
      this.ws = new WebSocket(WS_URL);
      
      this.ws.on('open', () => {
        console.log('✓ Connected to WebSocket');
        resolve();
      });
      
      this.ws.on('message', (data) => {
        const message = JSON.parse(data.toString());
        this.handleWebSocketMessage(message);
      });
      
      this.ws.on('error', reject);
    });
  }

  handleWebSocketMessage(message) {
    switch (message.type) {
      case 'initial_status':
        console.log('📊 Initial build status:', message.builds);
        break;
      case 'build_started':
        console.log(`🚀 Build started: ${message.buildId} (${message.language} → ${message.target})`);
        break;
      case 'build_progress':
        console.log(`⏳ Build progress: ${message.buildId} - ${message.progress}%`);
        break;
      case 'build_completed':
        console.log(`✅ Build completed: ${message.buildId}`);
        break;
      case 'build_failed':
        console.log(`❌ Build failed: ${message.buildId} - ${message.error}`);
        break;
    }
  }

  // Health check
  async health() {
    const response = await fetch(`${this.baseUrl}/health`);
    return response.json();
  }

  // Get system information
  async getSystemInfo() {
    const response = await fetch(`${this.baseUrl}/system`);
    return response.json();
  }

  // List projects
  async getProjects() {
    const response = await fetch(`${this.baseUrl}/projects`);
    return response.json();
  }

  // Get build status
  async getBuildStatus(buildId = null) {
    const url = buildId ? `${this.baseUrl}/status?buildId=${buildId}` : `${this.baseUrl}/status`;
    const response = await fetch(url);
    return response.json();
  }

  // Get build logs
  async getBuildLogs(buildId) {
    const response = await fetch(`${this.baseUrl}/logs/${buildId}`);
    return response.json();
  }

  // Trigger build for specific language
  async buildLanguage(language, options = {}) {
    const response = await fetch(`${this.baseUrl}/build/${language}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(options)
    });
    return response.json();
  }

  // Build all languages
  async buildAll(options = {}) {
    const response = await fetch(`${this.baseUrl}/build/all`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(options)
    });
    return response.json();
  }

  // List available modules
  async getModules() {
    const response = await fetch(`${this.baseUrl}/modules`);
    return response.json();
  }

  // Wait for build completion
  async waitForBuild(buildId, timeout = 60000) {
    const startTime = Date.now();
    
    while (Date.now() - startTime < timeout) {
      const status = await this.getBuildStatus(buildId);
      
      if (status.status === 'completed') {
        return { success: true, status };
      } else if (status.status === 'failed') {
        return { success: false, status };
      }
      
      // Wait 1 second before checking again
      await new Promise(resolve => setTimeout(resolve, 1000));
    }
    
    throw new Error(`Build ${buildId} timed out after ${timeout}ms`);
  }

  disconnect() {
    if (this.ws) {
      this.ws.close();
    }
  }
}

// Example usage
async function main() {
  const client = new PfApiClient();
  
  try {
    // Connect to WebSocket for real-time updates
    await client.connectWebSocket();
    
    // Check API health
    console.log('🏥 Health check:', await client.health());
    
    // Get system information
    console.log('💻 System info:', await client.getSystemInfo());
    
    // List projects
    console.log('📁 Projects:', await client.getProjects());
    
    // List existing modules
    console.log('📦 Existing modules:', await client.getModules());
    
    // Trigger a Rust build
    console.log('\n🦀 Starting Rust build...');
    const rustBuild = await client.buildLanguage('rust', { target: 'wasm' });
    console.log('Build queued:', rustBuild);
    
    // Wait for completion
    const result = await client.waitForBuild(rustBuild.buildId);
    if (result.success) {
      console.log('✅ Rust build completed successfully!');
      
      // Get build logs
      const logs = await client.getBuildLogs(rustBuild.buildId);
      console.log('📋 Build logs:', logs);
    } else {
      console.log('❌ Rust build failed:', result.status.error);
    }
    
    // Example: Build all languages
    console.log('\n🌐 Starting build for all languages...');
    const allBuilds = await client.buildAll({ target: 'wasm' });
    console.log('All builds queued:', allBuilds);
    
    // Check overall status
    setTimeout(async () => {
      const status = await client.getBuildStatus();
      console.log('📊 All build statuses:', status);
      client.disconnect();
    }, 5000);
    
  } catch (error) {
    console.error('❌ Error:', error.message);
    client.disconnect();
  }
}

// Run example if this file is executed directly
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch(console.error);
}

export default PfApiClient;