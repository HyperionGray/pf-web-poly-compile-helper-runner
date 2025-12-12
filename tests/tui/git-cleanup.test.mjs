#!/usr/bin/env node
/**
 * Git Cleanup TUI End-to-End Tests
 * 
 * Comprehensive test suite for the git-cleanup TUI tool
 * Tests all user workflows, error conditions, and edge cases
 */

import { TUITestFramework } from './framework/tui-test-framework.mjs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';
import { existsSync, mkdirSync, rmSync, writeFileSync } from 'node:fs';
import { execSync } from 'node:child_process';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const projectRoot = join(__dirname, '../../');
const gitCleanupTool = join(projectRoot, 'tools/git-cleanup.mjs');

// Test suite for git-cleanup TUI
const gitCleanupTests = TUITestFramework.createTestSuite('Git Cleanup TUI', [
  
  // Test 1: Basic workflow - analyze and select files
  {
    name: 'Basic workflow - analyze and select files for removal',
    async run(framework) {
      // Setup git mocks
      framework.setupGitMocks();
      
      // Add user interactions
      framework.addSelection('1 MB'); // Select threshold
      framework.addCheckboxSelection([0]); // Select first file
      framework.addConfirmation(true); // Confirm removal
      framework.addConfirmation(true); // Final confirmation
      
      // Run the test
      const result = await framework.runTUITest('node', [gitCleanupTool], {
        cwd: projectRoot
      });
      
      // Validate results
      framework.assertExitCode(result, 0);
      framework.assertOutputContains(result, 'Large Files in Git History');
      framework.assertOutputContains(result, 'Select files to remove');
      framework.assertOutputContains(result, 'Backup created');
      framework.assertOutputContains(result, 'Git history successfully cleaned');
    }
  },

  // Test 2: User cancellation workflow
  {
    name: 'User cancellation at file selection',
    async run(framework) {
      framework.setupGitMocks();
      
      // User selects threshold but cancels at file selection
      framework.addSelection('1 MB');
      framework.addCheckboxSelection([]); // Select no files
      
      const result = await framework.runTUITest('node', [gitCleanupTool], {
        cwd: projectRoot
      });
      
      framework.assertOutputContains(result, 'No files selected');
      framework.assertOutputContains(result, 'Operation cancelled');
    }
  },

  // Test 3: No large files found
  {
    name: 'No large files found scenario',
    async run(framework) {
      // Mock git commands to return no large files
      framework.mockCommand('git rev-parse --git-dir', ['.git']);
      framework.mockCommand('git rev-list --all --objects', ['abc123 small-file.txt']);
      framework.mockCommand('git cat-file --batch-check', ['blob abc123 1024 small-file.txt']);
      
      framework.addSelection('1 MB');
      
      const result = await framework.runTUITest('node', [gitCleanupTool], {
        cwd: projectRoot
      });
      
      framework.assertOutputContains(result, 'No files found larger than');
    }
  },

  // Test 4: Not a git repository error
  {
    name: 'Not a git repository error handling',
    async run(framework) {
      // Mock git command to fail
      framework.mockCommand('git rev-parse --git-dir', { error: 'Not a git repository' });
      
      const result = await framework.runTUITest('node', [gitCleanupTool], {
        cwd: '/tmp' // Non-git directory
      });
      
      framework.assertOutputContains(result, 'not a git repository');
      framework.assertExitCode(result, 1);
    }
  },

  // Test 5: Custom threshold input
  {
    name: 'Custom threshold input workflow',
    async run(framework) {
      framework.setupGitMocks();
      
      framework.addSelection('Custom'); // Select custom threshold
      framework.addTextInput('500KB'); // Enter custom size
      framework.addCheckboxSelection([0]); // Select first file
      framework.addConfirmation(true); // Confirm removal
      framework.addConfirmation(true); // Final confirmation
      
      const result = await framework.runTUITest('node', [gitCleanupTool], {
        cwd: projectRoot
      });
      
      framework.assertExitCode(result, 0);
      framework.assertOutputContains(result, 'Enter custom size');
    }
  },

  // Test 6: Multiple file selection
  {
    name: 'Multiple file selection workflow',
    async run(framework) {
      // Setup mocks with multiple large files
      framework.mockCommand('git rev-parse --git-dir', ['.git']);
      framework.mockCommand('git rev-list --all --objects', [
        'abc123 large-file1.zip',
        'def456 large-file2.zip',
        'ghi789 large-file3.zip'
      ]);
      framework.mockCommand('git cat-file --batch-check', [
        'blob abc123 50000000 large-file1.zip',
        'blob def456 40000000 large-file2.zip',
        'blob ghi789 30000000 large-file3.zip'
      ]);
      framework.mockCommand('git bundle create', ['Bundle created successfully']);
      framework.mockCommand('git-filter-repo --invert-paths', ['History rewritten successfully']);
      
      framework.addSelection('10 MB');
      framework.addCheckboxSelection([0, 2]); // Select first and third files
      framework.addConfirmation(true);
      framework.addConfirmation(true);
      
      const result = await framework.runTUITest('node', [gitCleanupTool], {
        cwd: projectRoot
      });
      
      framework.assertExitCode(result, 0);
      framework.assertOutputContains(result, 'large-file1.zip');
      framework.assertOutputContains(result, 'large-file3.zip');
    }
  },

  // Test 7: git-filter-repo not installed
  {
    name: 'git-filter-repo dependency missing',
    async run(framework) {
      framework.setupGitMocks();
      
      // Mock git-filter-repo command to fail
      framework.mockCommand('git-filter-repo --version', { error: 'command not found' });
      
      framework.addSelection('1 MB');
      framework.addCheckboxSelection([0]);
      framework.addConfirmation(true);
      framework.addConfirmation(true);
      
      const result = await framework.runTUITest('node', [gitCleanupTool], {
        cwd: projectRoot
      });
      
      framework.assertOutputContains(result, 'git-filter-repo');
      framework.assertOutputContains(result, 'not installed');
    }
  },

  // Test 8: Backup creation failure
  {
    name: 'Backup creation failure handling',
    async run(framework) {
      framework.setupGitMocks();
      
      // Mock backup command to fail
      framework.mockCommand('git bundle create', { error: 'Permission denied' });
      
      framework.addSelection('1 MB');
      framework.addCheckboxSelection([0]);
      framework.addConfirmation(true);
      framework.addConfirmation(true);
      
      const result = await framework.runTUITest('node', [gitCleanupTool], {
        cwd: projectRoot
      });
      
      framework.assertOutputContains(result, 'Failed to create backup');
    }
  },

  // Test 9: Large repository performance
  {
    name: 'Large repository with many files',
    async run(framework) {
      // Mock a repository with many large files
      const manyFiles = [];
      const manyObjects = [];
      
      for (let i = 0; i < 100; i++) {
        manyObjects.push(`file${i} large-file-${i}.bin`);
        manyFiles.push(`blob file${i} ${10000000 + i * 1000} large-file-${i}.bin`);
      }
      
      framework.mockCommand('git rev-parse --git-dir', ['.git']);
      framework.mockCommand('git rev-list --all --objects', manyObjects);
      framework.mockCommand('git cat-file --batch-check', manyFiles);
      framework.mockCommand('git bundle create', ['Bundle created successfully']);
      framework.mockCommand('git-filter-repo --invert-paths', ['History rewritten successfully']);
      
      framework.addSelection('5 MB');
      framework.addCheckboxSelection([0, 1, 2]); // Select first 3 files
      framework.addConfirmation(true);
      framework.addConfirmation(true);
      
      const result = await framework.runTUITest('node', [gitCleanupTool], {
        cwd: projectRoot,
        timeout: 60000 // Longer timeout for large repo
      });
      
      framework.assertExitCode(result, 0);
      framework.assertOutputContains(result, 'large-file-0.bin');
    }
  },

  // Test 10: Edge case - empty repository
  {
    name: 'Empty repository handling',
    async run(framework) {
      framework.mockCommand('git rev-parse --git-dir', ['.git']);
      framework.mockCommand('git rev-list --all --objects', []); // Empty repository
      framework.mockCommand('git cat-file --batch-check', []);
      
      framework.addSelection('1 MB');
      
      const result = await framework.runTUITest('node', [gitCleanupTool], {
        cwd: projectRoot
      });
      
      framework.assertOutputContains(result, 'No files found');
    }
  }
]);

// Export the test suite
export { gitCleanupTests };

// Run tests if this file is executed directly
if (import.meta.url === `file://${process.argv[1]}`) {
  gitCleanupTests.run().then(results => {
    process.exit(results.failed > 0 ? 1 : 0);
  }).catch(error => {
    console.error('Test suite failed:', error);
    process.exit(1);
  });
}