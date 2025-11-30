#!/usr/bin/env node
/**
 * TUI Testing Framework
 * 
 * A comprehensive framework for testing Terminal User Interface applications
 * Provides utilities for mocking user input, capturing output, and validating TUI behavior
 */

import { EventEmitter } from 'node:events';
import { spawn } from 'node:child_process';
import { createWriteStream } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { randomUUID } from 'node:crypto';

export class TUITestFramework extends EventEmitter {
  constructor(options = {}) {
    super();
    this.options = {
      timeout: 30000,
      captureOutput: true,
      mockGitCommands: true,
      mockFileSystem: true,
      ...options
    };
    
    this.mocks = new Map();
    this.interactions = [];
    this.output = [];
    this.currentProcess = null;
    this.testId = randomUUID();
  }

  /**
   * Mock a system command with predefined responses
   */
  mockCommand(command, responses) {
    this.mocks.set(command, responses);
  }

  /**
   * Mock git commands with common responses
   */
  setupGitMocks() {
    this.mockCommand('git rev-parse --git-dir', ['.git']);
    this.mockCommand('git rev-list --all --objects', [
      'abc123 large-file.zip',
      'def456 medium-file.png',
      'ghi789 small-file.txt'
    ]);
    this.mockCommand('git cat-file --batch-check', [
      'blob abc123 38465101 large-file.zip',
      'blob def456 1572864 medium-file.png', 
      'blob ghi789 1024 small-file.txt'
    ]);
    this.mockCommand('git bundle create', ['Bundle created successfully']);
    this.mockCommand('git-filter-repo --invert-paths', ['History rewritten successfully']);
  }

  /**
   * Simulate user input for prompts
   */
  addInteraction(type, value, delay = 100) {
    this.interactions.push({ type, value, delay });
  }

  /**
   * Add a selection interaction (for select prompts)
   */
  addSelection(value, delay = 100) {
    this.addInteraction('select', value, delay);
  }

  /**
   * Add a checkbox interaction (for multi-select prompts)
   */
  addCheckboxSelection(selections, delay = 100) {
    this.addInteraction('checkbox', selections, delay);
  }

  /**
   * Add a confirmation interaction
   */
  addConfirmation(value, delay = 100) {
    this.addInteraction('confirm', value, delay);
  }

  /**
   * Add text input interaction
   */
  addTextInput(value, delay = 100) {
    this.addInteraction('input', value, delay);
  }

  /**
   * Run a TUI application with mocked interactions
   */
  async runTUITest(command, args = [], options = {}) {
    return new Promise((resolve, reject) => {
      const testOptions = {
        stdio: ['pipe', 'pipe', 'pipe'],
        env: {
          ...process.env,
          NODE_ENV: 'test',
          TUI_TEST_MODE: 'true',
          TUI_TEST_ID: this.testId,
          ...options.env
        },
        cwd: options.cwd || process.cwd()
      };

      this.currentProcess = spawn(command, args, testOptions);
      
      let stdout = '';
      let stderr = '';
      let interactionIndex = 0;

      // Capture output
      this.currentProcess.stdout.on('data', (data) => {
        const chunk = data.toString();
        stdout += chunk;
        this.output.push({ type: 'stdout', data: chunk, timestamp: Date.now() });
        
        // Trigger interactions based on output patterns
        this.processOutput(chunk, interactionIndex);
      });

      this.currentProcess.stderr.on('data', (data) => {
        const chunk = data.toString();
        stderr += chunk;
        this.output.push({ type: 'stderr', data: chunk, timestamp: Date.now() });
      });

      // Handle interactions
      const sendInteraction = (interaction) => {
        setTimeout(() => {
          if (this.currentProcess && !this.currentProcess.killed) {
            this.sendInput(interaction);
          }
        }, interaction.delay);
      };

      // Process output and send appropriate inputs
      this.processOutput = (output, index) => {
        if (index < this.interactions.length) {
          const interaction = this.interactions[index];
          
          // Check if output indicates we should send this interaction
          if (this.shouldSendInteraction(output, interaction)) {
            sendInteraction(interaction);
            interactionIndex++;
          }
        }
      };

      this.currentProcess.on('close', (code) => {
        resolve({
          code,
          stdout,
          stderr,
          output: this.output,
          interactions: this.interactions
        });
      });

      this.currentProcess.on('error', (error) => {
        reject(error);
      });

      // Timeout handling
      setTimeout(() => {
        if (this.currentProcess && !this.currentProcess.killed) {
          this.currentProcess.kill();
          reject(new Error(`Test timed out after ${this.options.timeout}ms`));
        }
      }, this.options.timeout);
    });
  }

  /**
   * Determine if we should send an interaction based on output
   */
  shouldSendInteraction(output, interaction) {
    // Look for common prompt patterns
    const patterns = {
      select: /\?\s*Select|Choose/i,
      checkbox: /\?\s*Select.*files|Select.*remove/i,
      confirm: /\?\s*Are you sure|Proceed|Continue/i,
      input: /\?\s*Enter|Input|Type/i
    };

    return patterns[interaction.type]?.test(output) || false;
  }

  /**
   * Send input to the process based on interaction type
   */
  sendInput(interaction) {
    if (!this.currentProcess || this.currentProcess.killed) return;

    switch (interaction.type) {
      case 'select':
        // Send arrow keys and enter for selection
        this.currentProcess.stdin.write('\x1B[B'); // Down arrow
        this.currentProcess.stdin.write('\r'); // Enter
        break;
        
      case 'checkbox':
        // Send space to toggle selections, then enter
        if (Array.isArray(interaction.value)) {
          interaction.value.forEach(() => {
            this.currentProcess.stdin.write(' '); // Space to toggle
            this.currentProcess.stdin.write('\x1B[B'); // Down arrow
          });
        }
        this.currentProcess.stdin.write('\r'); // Enter
        break;
        
      case 'confirm':
        // Send y/n for confirmation
        this.currentProcess.stdin.write(interaction.value ? 'y' : 'n');
        this.currentProcess.stdin.write('\r');
        break;
        
      case 'input':
        // Send text input
        this.currentProcess.stdin.write(interaction.value);
        this.currentProcess.stdin.write('\r');
        break;
    }
  }

  /**
   * Validate TUI output contains expected content
   */
  assertOutputContains(result, expectedContent) {
    const fullOutput = result.stdout + result.stderr;
    if (!fullOutput.includes(expectedContent)) {
      throw new Error(`Expected output to contain "${expectedContent}", but got: ${fullOutput}`);
    }
  }

  /**
   * Validate TUI output matches pattern
   */
  assertOutputMatches(result, pattern) {
    const fullOutput = result.stdout + result.stderr;
    if (!pattern.test(fullOutput)) {
      throw new Error(`Expected output to match pattern ${pattern}, but got: ${fullOutput}`);
    }
  }

  /**
   * Validate exit code
   */
  assertExitCode(result, expectedCode) {
    if (result.code !== expectedCode) {
      throw new Error(`Expected exit code ${expectedCode}, but got ${result.code}`);
    }
  }

  /**
   * Validate that specific prompts appeared
   */
  assertPromptsAppeared(result, expectedPrompts) {
    const fullOutput = result.stdout + result.stderr;
    expectedPrompts.forEach(prompt => {
      if (!fullOutput.includes(prompt)) {
        throw new Error(`Expected prompt "${prompt}" to appear in output`);
      }
    });
  }

  /**
   * Clean up test resources
   */
  cleanup() {
    if (this.currentProcess && !this.currentProcess.killed) {
      this.currentProcess.kill();
    }
    this.mocks.clear();
    this.interactions = [];
    this.output = [];
  }

  /**
   * Create a test suite for TUI applications
   */
  static createTestSuite(name, tests) {
    return {
      name,
      tests,
      async run() {
        console.log(`\n🧪 Running TUI Test Suite: ${name}`);
        let passed = 0;
        let failed = 0;
        
        for (const test of tests) {
          const framework = new TUITestFramework();
          try {
            console.log(`  ▶️  ${test.name}`);
            await test.run(framework);
            console.log(`  ✅ ${test.name} - PASSED`);
            passed++;
          } catch (error) {
            console.log(`  ❌ ${test.name} - FAILED: ${error.message}`);
            failed++;
          } finally {
            framework.cleanup();
          }
        }
        
        console.log(`\n📊 Results: ${passed} passed, ${failed} failed`);
        return { passed, failed, total: tests.length };
      }
    };
  }
}

export default TUITestFramework;