#!/usr/bin/env node
/**
 * Comprehensive Unit Tests for pf Sync and System Operations
 * 
 * Tests sync statements, service management, package management, and file operations
 */

import { spawn } from 'child_process';
import { promises as fs } from 'fs';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';
import os from 'os';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const projectRoot = join(__dirname, '../..');
const pfRunnerDir = join(projectRoot, 'pf-runner');

// Test utilities
class SyncOpsTester {
    constructor() {
        this.passed = 0;
        this.failed = 0;
        this.tests = [];
    }

    async runPfParser(pfContent, action = 'list') {
        const tmpFile = join(os.tmpdir(), `pf-sync-test-${Date.now()}.pf`);
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

    async testSyntaxValid(name, pfContent) {
        await this.test(name, async () => {
            const result = await this.runPfParser(pfContent);
            if (result.code !== 0) {
                throw new Error(`Syntax validation failed: ${result.stderr || result.stdout}`);
            }
        });
    }

    async testSyntaxInvalid(name, pfContent) {
        await this.test(name, async () => {
            const result = await this.runPfParser(pfContent);
            if (result.code === 0) {
                throw new Error(`Expected syntax error but parsing succeeded`);
            }
        });
    }
}

// Test cases
async function runTests() {
    const tester = new SyncOpsTester();
    
    console.log('🔍 pf Sync & System Operations Unit Tests');
    console.log('==========================================\n');

    // ==========================================
    // SECTION 1: Basic Sync Operations
    // ==========================================
    console.log('\n--- Section 1: Basic Sync Operations ---');

    await tester.testSyntaxValid('Basic local sync', `
task sync-local
  describe Sync files locally
  sync src="/source/path" dst="/dest/path"
end
`);

    await tester.testSyntaxValid('Sync with SSH destination', `
task sync-remote
  describe Sync to remote server
  sync src="/local/path" dst="user@host:/remote/path"
end
`);

    await tester.testSyntaxValid('Sync with verbose flag', `
task sync-verbose
  describe Verbose sync
  sync src="/local" dst="/remote" verbose
end
`);

    await tester.testSyntaxValid('Sync with recursive flag', `
task sync-recursive
  describe Recursive sync
  sync src="/local" dst="/remote" recursive
end
`);

    await tester.testSyntaxValid('Sync with delete flag', `
task sync-delete
  describe Sync with delete
  sync src="/local" dst="/remote" delete
end
`);

    await tester.testSyntaxValid('Sync with all flags', `
task sync-full
  describe Full sync options
  sync src="/local" dst="/remote" verbose recursive delete
end
`);

    await tester.testSyntaxValid('Sync with SSH port', `
task sync-port
  describe Sync with custom SSH port
  sync src="/local" dst="user@host:/remote" port="2222"
end
`);

    await tester.testSyntaxValid('Sync with excludes', `
task sync-excludes
  describe Sync with excludes
  sync src="/local" dst="/remote" excludes=["*.log", "*.tmp", ".git"]
end
`);

    await tester.testSyntaxValid('Sync with exclude file', `
task sync-exclude-file
  describe Sync with exclude file
  sync src="/local" dst="/remote" exclude_file=".rsyncignore"
end
`);

    await tester.testSyntaxValid('Sync dry run', `
task sync-dry
  describe Sync dry run
  sync src="/local" dst="/remote" dry
end
`);

    // ==========================================
    // SECTION 2: Package Management
    // ==========================================
    console.log('\n--- Section 2: Package Management ---');

    await tester.testSyntaxValid('Install single package', `
task install-pkg
  describe Install single package
  packages install nginx
end
`);

    await tester.testSyntaxValid('Install multiple packages', `
task install-multi
  describe Install multiple packages
  packages install nginx postgresql redis
end
`);

    await tester.testSyntaxValid('Remove single package', `
task remove-pkg
  describe Remove single package
  packages remove nginx
end
`);

    await tester.testSyntaxValid('Remove multiple packages', `
task remove-multi
  describe Remove multiple packages
  packages remove nginx postgresql redis
end
`);

    await tester.testSyntaxValid('Install development tools', `
task install-dev
  describe Install development tools
  packages install build-essential gcc g++ make cmake git
end
`);

    await tester.testSyntaxValid('Install with hyphens in name', `
task install-hyphen
  describe Install package with hyphen
  packages install build-essential libssl-dev libffi-dev
end
`);

    await tester.testSyntaxValid('Mixed package operations', `
task manage-pkgs
  describe Mixed package operations
  packages remove old-package
  packages install new-package
end
`);

    // ==========================================
    // SECTION 3: Service Management
    // ==========================================
    console.log('\n--- Section 3: Service Management ---');

    await tester.testSyntaxValid('Service start', `
task start-svc
  describe Start a service
  service start nginx
end
`);

    await tester.testSyntaxValid('Service stop', `
task stop-svc
  describe Stop a service
  service stop nginx
end
`);

    await tester.testSyntaxValid('Service restart', `
task restart-svc
  describe Restart a service
  service restart nginx
end
`);

    await tester.testSyntaxValid('Service enable', `
task enable-svc
  describe Enable a service
  service enable nginx
end
`);

    await tester.testSyntaxValid('Service disable', `
task disable-svc
  describe Disable a service
  service disable nginx
end
`);

    await tester.testSyntaxValid('Multiple service operations', `
task manage-services
  describe Multiple service operations
  service stop nginx
  service stop postgresql
  service start redis
  service enable redis
end
`);

    await tester.testSyntaxValid('Service with hyphenated name', `
task manage-hyphen-svc
  describe Manage hyphenated service
  service start docker-compose
end
`);

    await tester.testSyntaxValid('Full service lifecycle', `
task service-lifecycle
  describe Full service lifecycle
  service stop myapp
  shell echo "Updating configuration..."
  service start myapp
  service enable myapp
end
`);

    // ==========================================
    // SECTION 4: Directory Operations
    // ==========================================
    console.log('\n--- Section 4: Directory Operations ---');

    await tester.testSyntaxValid('Create directory', `
task create-dir
  describe Create a directory
  directory /tmp/myapp
end
`);

    await tester.testSyntaxValid('Create directory with mode', `
task create-dir-mode
  describe Create directory with mode
  directory /var/log/myapp mode=0755
end
`);

    await tester.testSyntaxValid('Create multiple directories', `
task create-dirs
  describe Create multiple directories
  directory /opt/myapp
  directory /opt/myapp/bin mode=0755
  directory /opt/myapp/etc mode=0750
  directory /opt/myapp/var mode=0700
end
`);

    await tester.testSyntaxValid('Create nested directory', `
task create-nested
  describe Create nested directory
  directory /opt/myapp/deep/nested/path mode=0755
end
`);

    await tester.testSyntaxValid('Create directory with restrictive mode', `
task create-secure-dir
  describe Create secure directory
  directory /etc/secrets mode=0700
end
`);

    // ==========================================
    // SECTION 5: File Copy Operations
    // ==========================================
    console.log('\n--- Section 5: File Copy Operations ---');

    await tester.testSyntaxValid('Basic file copy', `
task copy-file
  describe Copy a file
  copy config.conf /etc/myapp/config.conf
end
`);

    await tester.testSyntaxValid('Copy with mode', `
task copy-mode
  describe Copy with mode
  copy config.conf /etc/myapp/ mode=0644
end
`);

    await tester.testSyntaxValid('Copy with owner', `
task copy-owner
  describe Copy with owner
  copy config.conf /etc/myapp/ user=root group=root
end
`);

    await tester.testSyntaxValid('Copy with all options', `
task copy-full
  describe Copy with all options
  copy config.conf /etc/myapp/ mode=0644 user=www-data group=www-data
end
`);

    await tester.testSyntaxValid('Multiple file copies', `
task copy-multi
  describe Copy multiple files
  copy app.conf /etc/myapp/ mode=0644
  copy secret.key /etc/myapp/ mode=0600 user=root
  copy script.sh /usr/local/bin/ mode=0755
end
`);

    // ==========================================
    // SECTION 6: Combined System Operations
    // ==========================================
    console.log('\n--- Section 6: Combined System Operations ---');

    await tester.testSyntaxValid('Setup new service', `
task setup-service
  describe Setup a new service
  packages install myapp-server
  directory /var/log/myapp mode=0755
  directory /etc/myapp mode=0755
  copy myapp.conf /etc/myapp/ mode=0644
  service enable myapp
  service start myapp
end
`);

    await tester.testSyntaxValid('Deploy application', `
task deploy
  describe Deploy application
  service stop myapp
  sync src="./dist" dst="/opt/myapp" recursive
  copy config.json /opt/myapp/ mode=0644
  service start myapp
end
`);

    await tester.testSyntaxValid('Server setup', `
task server-setup
  describe Full server setup
  packages install nginx postgresql redis
  directory /var/www/app mode=0755
  directory /var/log/app mode=0755
  copy nginx.conf /etc/nginx/sites-available/app
  copy pg_hba.conf /etc/postgresql/main/
  service restart nginx
  service restart postgresql
  service enable redis
  service start redis
end
`);

    // ==========================================
    // SECTION 7: Sync with Variables
    // ==========================================
    console.log('\n--- Section 7: Sync with Variables ---');

    await tester.testSyntaxValid('Sync with source variable', `
task sync-var-src src="./build"
  describe Sync with source variable
  sync src="$src" dst="/opt/app"
end
`);

    await tester.testSyntaxValid('Sync with destination variable', `
task sync-var-dst dst="/opt/app"
  describe Sync with destination variable
  sync src="./build" dst="$dst"
end
`);

    await tester.testSyntaxValid('Sync with host variable', `
task sync-var-host host="server1.example.com" user="deploy"
  describe Sync with host variable
  sync src="./dist" dst="$user@$host:/var/www/app"
end
`);

    // ==========================================
    // SECTION 8: Conditional Operations
    // ==========================================
    console.log('\n--- Section 8: Conditional Operations ---');

    await tester.testSyntaxValid('Conditional package install', `
task conditional-install install_deps="true"
  describe Conditional package install
  if $install_deps == "true"
    packages install build-essential cmake git
  end
end
`);

    await tester.testSyntaxValid('Environment-based service', `
task env-service env="prod"
  describe Environment-based service management
  if $env == "prod"
    service restart nginx
    service restart postgresql
  else
    service restart nginx-dev
  end
end
`);

    await tester.testSyntaxValid('Conditional sync', `
task conditional-sync sync_enabled="true"
  describe Conditional sync
  if $sync_enabled == "true"
    sync src="./dist" dst="/opt/app" recursive
  else
    shell echo "Sync skipped"
  end
end
`);

    // ==========================================
    // SECTION 9: Loop-based Operations
    // ==========================================
    console.log('\n--- Section 9: Loop-based Operations ---');

    await tester.testSyntaxValid('Multiple host sync', `
task multi-host-sync
  describe Sync to multiple hosts
  for host in ["host1.example.com", "host2.example.com", "host3.example.com"]
    sync src="./dist" dst="deploy@$host:/var/www/app" recursive
  end
end
`);

    await tester.testSyntaxValid('Multiple service management', `
task multi-service
  describe Manage multiple services
  for svc in ["nginx", "postgresql", "redis"]
    service restart $svc
  end
end
`);

    await tester.testSyntaxValid('Multiple directory creation', `
task multi-dir
  describe Create multiple directories
  for dir in ["bin", "lib", "etc", "var", "log"]
    directory /opt/myapp/$dir mode=0755
  end
end
`);

    // ==========================================
    // SECTION 10: Error Handling Patterns
    // ==========================================
    console.log('\n--- Section 10: Error Handling Patterns ---');

    await tester.testSyntaxValid('Safe service restart', `
task safe-restart
  describe Safe service restart with checks
  shell systemctl is-active --quiet myapp && echo "Service is running"
  service stop myapp
  shell sleep 2
  service start myapp
  shell systemctl is-active --quiet myapp || echo "Warning: Service may have failed to start"
end
`);

    await tester.testSyntaxValid('Sync with verification', `
task sync-verify
  describe Sync with verification
  sync src="./dist" dst="/opt/app" verbose
  shell ls -la /opt/app
  shell echo "Sync completed"
end
`);

    // ==========================================
    // SECTION 11: Invalid Syntax Tests
    // ==========================================
    console.log('\n--- Section 11: Invalid Syntax Tests ---');

    await tester.testSyntaxInvalid('Invalid service action', `
task invalid-svc
  describe Invalid service action
  service invalid nginx
end
`);

    await tester.testSyntaxInvalid('Invalid package action', `
task invalid-pkg
  describe Invalid package action
  packages invalid nginx
end
`);

    await tester.testSyntaxInvalid('Sync missing src', `
task sync-missing-src
  describe Sync missing source
  sync dst="/remote/path"
end
`);

    await tester.testSyntaxInvalid('Sync missing dst', `
task sync-missing-dst
  describe Sync missing destination
  sync src="/local/path"
end
`);

    // ==========================================
    // SECTION 12: Edge Cases
    // ==========================================
    console.log('\n--- Section 12: Edge Cases ---');

    await tester.testSyntaxValid('Directory with spaces in path', `
task dir-spaces
  describe Directory with spaces
  directory "/opt/my app" mode=0755
end
`);

    await tester.testSyntaxValid('Sync with special characters', `
task sync-special
  describe Sync with special chars
  sync src="/path/with-hyphen_underscore" dst="/dest/path"
end
`);

    await tester.testSyntaxValid('Service with number in name', `
task svc-number
  describe Service with number
  service start myapp2
end
`);

    await tester.testSyntaxValid('Package with version-like name', `
task pkg-version
  describe Package with version-like name
  packages install python3.11
end
`);

    // Print summary
    console.log('\n=============================');
    console.log('📊 Sync & Ops Test Results');
    console.log('=============================');
    console.log(`✅ Passed: ${tester.passed}`);
    console.log(`❌ Failed: ${tester.failed}`);
    console.log(`📈 Success Rate: ${Math.round((tester.passed / (tester.passed + tester.failed)) * 100)}%`);

    if (tester.failed === 0) {
        console.log('\n🎉 All sync & ops tests passed!');
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

export { runTests, SyncOpsTester };
