#!/usr/bin/env node
/**
 * TUI Integration Test
 * 
 * Quick integration test to verify TUI testing framework works correctly
 */

import { TUITestFramework } from './framework/tui-test-framework.mjs';
import GitCleanupTool from '../../tools/git-cleanup-testable.mjs';

async function runIntegrationTest() {
  console.log('🔧 Running TUI Integration Test...\n');
  
  try {
    // Test 1: Framework instantiation
    console.log('1. Testing framework instantiation...');
    const framework = new TUITestFramework();
    console.log('   ✅ Framework created successfully');
    
    // Test 2: Mock system
    console.log('2. Testing mock system...');
    framework.setupGitMocks();
    console.log('   ✅ Git mocks configured');
    
    // Test 3: Testable tool instantiation
    console.log('3. Testing testable tool...');
    
    // Create mock dependencies
    const mockDeps = {
      execSync: (cmd) => {
        if (cmd.includes('git rev-parse')) return '.git';
        if (cmd.includes('git-filter-repo --version')) return 'git-filter-repo 2.34.0';
        if (cmd.includes('git rev-list')) return 'abc123 test-file.zip';
        if (cmd.includes('git cat-file')) return 'blob abc123 10485760 test-file.zip';
        return '';
      },
      fs: {
        existsSync: () => false,
        mkdirSync: () => {},
        writeFileSync: () => {},
        unlinkSync: () => {}
      },
      prompts: {
        select: async () => 1024 * 1024, // 1MB threshold
        checkbox: async () => [0], // Select first file
        confirm: async () => false, // Cancel operation
        input: async () => '1MB'
      },
      ora: (text) => ({
        start: () => ({ succeed: () => {}, fail: () => {} }),
        succeed: () => {},
        fail: () => {}
      }),
      chalk: {
        blue: (text) => text,
        red: (text) => text,
        green: (text) => text,
        yellow: (text) => text,
        cyan: (text) => text
      },
      console: {
        log: () => {} // Silent for test
      },
      process: {
        cwd: () => '/test',
        exit: () => {},
        pid: 12345
      }
    };
    
    const tool = new GitCleanupTool(mockDeps);
    console.log('   ✅ Testable tool created successfully');
    
    // Test 4: Basic tool functionality
    console.log('4. Testing basic tool methods...');
    const bytes = tool.formatBytes(1048576);
    if (bytes !== '1 MB') {
      throw new Error(`Expected '1 MB', got '${bytes}'`);
    }
    console.log('   ✅ formatBytes method works correctly');
    
    // Test 5: Mock execution
    console.log('5. Testing mock execution...');
    const result = tool.execCommand('git rev-parse --git-dir');
    if (result !== '.git') {
      throw new Error(`Expected '.git', got '${result}'`);
    }
    console.log('   ✅ Mock execution works correctly');
    
    // Test 6: Framework test creation
    console.log('6. Testing framework test creation...');
    const testSuite = TUITestFramework.createTestSuite('Integration Test', [
      {
        name: 'Sample test',
        async run(fw) {
          fw.setupGitMocks();
          // This is just a structure test
          return true;
        }
      }
    ]);
    
    if (!testSuite.name || !testSuite.tests || !testSuite.run) {
      throw new Error('Test suite structure is invalid');
    }
    console.log('   ✅ Test suite creation works correctly');
    
    console.log('\n🎉 All integration tests passed!');
    console.log('\n📋 Integration Test Summary:');
    console.log('   ✅ TUI Testing Framework: Ready');
    console.log('   ✅ Mock System: Functional');
    console.log('   ✅ Testable Tool: Working');
    console.log('   ✅ Test Suite Creation: Operational');
    console.log('   ✅ Dependency Injection: Successful');
    console.log('   ✅ Framework Integration: Complete');
    
    return true;
    
  } catch (error) {
    console.error('\n❌ Integration test failed:', error.message);
    console.error('\n🔍 This indicates an issue with the TUI testing setup.');
    console.error('   Please check the framework implementation.');
    return false;
  }
}

// Run integration test if this file is executed directly
if (import.meta.url === `file://${process.argv[1]}`) {
  runIntegrationTest().then(success => {
    process.exit(success ? 0 : 1);
  }).catch(error => {
    console.error('Integration test execution failed:', error);
    process.exit(1);
  });
}

export { runIntegrationTest };