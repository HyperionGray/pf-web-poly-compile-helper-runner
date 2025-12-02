#!/usr/bin/env node
/**
 * Comprehensive Unit Tests for pf Build System Helpers
 * 
 * Tests all build system integrations: makefile, cmake, meson, cargo, go, etc.
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
class BuildHelperTester {
    constructor() {
        this.passed = 0;
        this.failed = 0;
        this.tests = [];
    }

    async runPfParser(pfContent, action = 'list') {
        const tmpFile = join(os.tmpdir(), `pf-build-test-${Date.now()}.pf`);
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
}

// Test cases
async function runTests() {
    const tester = new BuildHelperTester();
    
    console.log('🔍 pf Build System Helpers Unit Tests');
    console.log('=====================================\n');

    // ==========================================
    // SECTION 1: Makefile/Make
    // ==========================================
    console.log('\n--- Section 1: Makefile/Make ---');

    await tester.testSyntaxValid('Basic make command', `
task build-make
  describe Build with make
  makefile
end
`);

    await tester.testSyntaxValid('Make with target', `
task build-make-target
  describe Build with make target
  makefile all
end
`);

    await tester.testSyntaxValid('Make with multiple targets', `
task build-make-multi
  describe Build with multiple make targets
  makefile clean all install
end
`);

    await tester.testSyntaxValid('Make with variable', `
task build-make-var
  describe Build with make variable
  make PREFIX=/usr/local
end
`);

    await tester.testSyntaxValid('Make with jobs', `
task build-make-jobs
  describe Build with parallel jobs
  make -j4 all
end
`);

    await tester.testSyntaxValid('Make clean and build', `
task rebuild
  describe Clean and rebuild
  make clean
  make all
end
`);

    await tester.testSyntaxValid('Make with verbose', `
task build-verbose
  describe Verbose make build
  make V=1 all
end
`);

    // ==========================================
    // SECTION 2: CMake
    // ==========================================
    console.log('\n--- Section 2: CMake ---');

    await tester.testSyntaxValid('Basic cmake', `
task build-cmake
  describe Build with cmake
  cmake
end
`);

    await tester.testSyntaxValid('CMake with source dir', `
task build-cmake-src
  describe Build with cmake source dir
  cmake .
end
`);

    await tester.testSyntaxValid('CMake with build type', `
task build-cmake-release
  describe CMake release build
  cmake -DCMAKE_BUILD_TYPE=Release
end
`);

    await tester.testSyntaxValid('CMake with debug build', `
task build-cmake-debug
  describe CMake debug build
  cmake -DCMAKE_BUILD_TYPE=Debug
end
`);

    await tester.testSyntaxValid('CMake with install prefix', `
task build-cmake-prefix
  describe CMake with install prefix
  cmake -DCMAKE_INSTALL_PREFIX=/opt/myapp
end
`);

    await tester.testSyntaxValid('CMake with generator', `
task build-cmake-ninja
  describe CMake with Ninja generator
  cmake -G Ninja
end
`);

    await tester.testSyntaxValid('CMake with multiple options', `
task build-cmake-full
  describe CMake with multiple options
  cmake -DCMAKE_BUILD_TYPE=Release -DBUILD_TESTS=ON -DBUILD_DOCS=OFF
end
`);

    // ==========================================
    // SECTION 3: Meson
    // ==========================================
    console.log('\n--- Section 3: Meson ---');

    await tester.testSyntaxValid('Basic meson setup', `
task build-meson
  describe Build with meson
  meson setup builddir
end
`);

    await tester.testSyntaxValid('Meson compile', `
task compile-meson
  describe Compile with meson
  meson compile -C builddir
end
`);

    await tester.testSyntaxValid('Ninja build', `
task build-ninja
  describe Build with ninja
  ninja -C builddir
end
`);

    await tester.testSyntaxValid('Meson with buildtype', `
task build-meson-release
  describe Meson release build
  meson setup builddir --buildtype=release
end
`);

    await tester.testSyntaxValid('Meson with options', `
task build-meson-opts
  describe Meson with options
  meson setup builddir -Doption1=value1 -Doption2=value2
end
`);

    await tester.testSyntaxValid('Meson reconfigure', `
task reconfig-meson
  describe Meson reconfigure
  meson setup builddir --reconfigure
end
`);

    // ==========================================
    // SECTION 4: Cargo (Rust)
    // ==========================================
    console.log('\n--- Section 4: Cargo (Rust) ---');

    await tester.testSyntaxValid('Basic cargo build', `
task build-cargo
  describe Build with cargo
  cargo build
end
`);

    await tester.testSyntaxValid('Cargo release build', `
task build-cargo-release
  describe Cargo release build
  cargo build --release
end
`);

    await tester.testSyntaxValid('Cargo test', `
task test-cargo
  describe Run cargo tests
  cargo test
end
`);

    await tester.testSyntaxValid('Cargo run', `
task run-cargo
  describe Run cargo project
  cargo run
end
`);

    await tester.testSyntaxValid('Cargo with features', `
task build-cargo-features
  describe Cargo with features
  cargo build --features "feature1 feature2"
end
`);

    await tester.testSyntaxValid('Cargo with target', `
task build-cargo-wasm
  describe Cargo WASM target
  cargo build --target wasm32-unknown-unknown
end
`);

    await tester.testSyntaxValid('Cargo clippy', `
task lint-cargo
  describe Run cargo clippy
  cargo clippy
end
`);

    await tester.testSyntaxValid('Cargo fmt', `
task format-cargo
  describe Format with cargo fmt
  cargo fmt
end
`);

    await tester.testSyntaxValid('Cargo doc', `
task doc-cargo
  describe Generate docs with cargo
  cargo doc
end
`);

    await tester.testSyntaxValid('Cargo clean', `
task clean-cargo
  describe Clean cargo artifacts
  cargo clean
end
`);

    // ==========================================
    // SECTION 5: Go
    // ==========================================
    console.log('\n--- Section 5: Go ---');

    await tester.testSyntaxValid('Basic go build', `
task build-go
  describe Build with go
  go_build
end
`);

    await tester.testSyntaxValid('Go build with output', `
task build-go-out
  describe Go build with output
  go_build -o myapp main.go
end
`);

    await tester.testSyntaxValid('Go build alternative syntax', `
task build-gobuild
  describe Go build alternative
  gobuild -o app ./cmd/main
end
`);

    await tester.testSyntaxValid('Go build with ldflags', `
task build-go-ldflags
  describe Go build with ldflags
  go_build -ldflags="-s -w"
end
`);

    await tester.testSyntaxValid('Go build with tags', `
task build-go-tags
  describe Go build with tags
  go_build -tags "production,cgo"
end
`);

    await tester.testSyntaxValid('Go build race detector', `
task build-go-race
  describe Go build with race detector
  go_build -race
end
`);

    // ==========================================
    // SECTION 6: Configure (Autotools)
    // ==========================================
    console.log('\n--- Section 6: Configure (Autotools) ---');

    await tester.testSyntaxValid('Basic configure', `
task build-configure
  describe Configure with defaults
  configure
end
`);

    await tester.testSyntaxValid('Configure with prefix', `
task build-configure-prefix
  describe Configure with prefix
  configure --prefix=/usr/local
end
`);

    await tester.testSyntaxValid('Configure with enable flag', `
task build-configure-enable
  describe Configure with enable
  configure --enable-shared --enable-static
end
`);

    await tester.testSyntaxValid('Configure with disable flag', `
task build-configure-disable
  describe Configure with disable
  configure --disable-docs --disable-tests
end
`);

    await tester.testSyntaxValid('Configure with with flag', `
task build-configure-with
  describe Configure with with
  configure --with-openssl=/opt/openssl
end
`);

    await tester.testSyntaxValid('Configure full example', `
task build-configure-full
  describe Full configure example
  configure --prefix=/usr --sysconfdir=/etc --enable-shared --disable-static --with-ssl
end
`);

    // ==========================================
    // SECTION 7: Just
    // ==========================================
    console.log('\n--- Section 7: Just ---');

    await tester.testSyntaxValid('Basic just', `
task build-just
  describe Build with just
  justfile
end
`);

    await tester.testSyntaxValid('Just with recipe', `
task build-just-recipe
  describe Just with recipe
  justfile build
end
`);

    await tester.testSyntaxValid('Just alternative syntax', `
task build-just-alt
  describe Just alternative syntax
  just test
end
`);

    await tester.testSyntaxValid('Just with arguments', `
task build-just-args
  describe Just with arguments
  just deploy production
end
`);

    await tester.testSyntaxValid('Just with multiple recipes', `
task build-just-multi
  describe Just with multiple recipes
  just clean build test
end
`);

    // ==========================================
    // SECTION 8: Autobuild
    // ==========================================
    console.log('\n--- Section 8: Autobuild ---');

    await tester.testSyntaxValid('Basic autobuild', `
task auto
  describe Automatic build detection
  autobuild
end
`);

    await tester.testSyntaxValid('Autobuild alternative syntax', `
task auto-alt
  describe Autobuild alternative
  auto_build
end
`);

    await tester.testSyntaxValid('Autobuild with options', `
task auto-opts
  describe Autobuild with options
  autobuild --verbose
end
`);

    // ==========================================
    // SECTION 9: Build Detect
    // ==========================================
    console.log('\n--- Section 9: Build Detect ---');

    await tester.testSyntaxValid('Basic build detect', `
task detect
  describe Detect build system
  build_detect
end
`);

    await tester.testSyntaxValid('Detect build alternative syntax', `
task detect-alt
  describe Detect build alternative
  detect_build
end
`);

    // ==========================================
    // SECTION 10: Combined Build Pipelines
    // ==========================================
    console.log('\n--- Section 10: Combined Build Pipelines ---');

    await tester.testSyntaxValid('CMake pipeline', `
task build-cmake-pipeline
  describe Full CMake build pipeline
  cmake -B build -DCMAKE_BUILD_TYPE=Release
  shell cmake --build build -j4
  shell cmake --install build
end
`);

    await tester.testSyntaxValid('Rust release pipeline', `
task release-rust
  describe Rust release pipeline
  cargo fmt
  cargo clippy
  cargo test
  cargo build --release
end
`);

    await tester.testSyntaxValid('Go CI pipeline', `
task ci-go
  describe Go CI pipeline
  shell go mod tidy
  shell go fmt ./...
  shell go vet ./...
  shell go test ./...
  go_build -o bin/app
end
`);

    await tester.testSyntaxValid('Autotools pipeline', `
task build-autotools
  describe Autotools build pipeline
  shell autoreconf -i
  configure --prefix=/usr/local
  make clean
  make -j4
  make install
end
`);

    await tester.testSyntaxValid('Meson pipeline', `
task build-meson-pipe
  describe Meson build pipeline
  meson setup builddir --buildtype=release
  ninja -C builddir
  shell ninja -C builddir test
  shell ninja -C builddir install
end
`);

    await tester.testSyntaxValid('Multi-language project', `
task build-multi
  describe Multi-language project build
  shell echo "Building frontend..."
  shell npm run build
  shell echo "Building backend..."
  cargo build --release
  shell echo "Building CLI..."
  go_build -o cli ./cmd/cli
end
`);

    // ==========================================
    // SECTION 11: Conditional Builds
    // ==========================================
    console.log('\n--- Section 11: Conditional Builds ---');

    await tester.testSyntaxValid('Conditional build type', `
task build mode="debug"
  describe Conditional build type
  if $mode == "release"
    cargo build --release
  else
    cargo build
  end
end
`);

    await tester.testSyntaxValid('Platform-specific build', `
task build-platform platform="linux"
  describe Platform-specific build
  if $platform == "windows"
    shell echo "Building for Windows"
    cargo build --target x86_64-pc-windows-msvc
  else
    shell echo "Building for Unix"
    cargo build
  end
end
`);

    await tester.testSyntaxValid('Feature flag build', `
task build-features enable_ssl="true" enable_compression="false"
  describe Feature flag build
  if $enable_ssl == "true"
    shell echo "SSL enabled"
    cargo build --features ssl
  end
  if $enable_compression == "true"
    shell echo "Compression enabled"
    cargo build --features compression
  end
end
`);

    // ==========================================
    // SECTION 12: Build with Environment
    // ==========================================
    console.log('\n--- Section 12: Build with Environment ---');

    await tester.testSyntaxValid('Build with CC env', `
task build-cc
  describe Build with custom compiler
  env CC=clang CXX=clang++
  cmake -B build
  make -C build
end
`);

    await tester.testSyntaxValid('Build with CFLAGS', `
task build-cflags
  describe Build with custom flags
  env CFLAGS="-O3 -march=native" LDFLAGS="-static"
  configure
  make
end
`);

    await tester.testSyntaxValid('Build with GOPATH', `
task build-gopath
  describe Build with GOPATH
  env GOPATH=/custom/gopath GOOS=linux GOARCH=amd64
  go_build -o app
end
`);

    await tester.testSyntaxValid('Build with Rust env', `
task build-rust-env
  describe Build with Rust environment
  env CARGO_TARGET_DIR=./target RUSTFLAGS="-C target-cpu=native"
  cargo build --release
end
`);

    // ==========================================
    // SECTION 13: Cross Compilation
    // ==========================================
    console.log('\n--- Section 13: Cross Compilation ---');

    await tester.testSyntaxValid('Rust cross compile', `
task cross-rust target="x86_64-unknown-linux-musl"
  describe Rust cross compilation
  cargo build --release --target $target
end
`);

    await tester.testSyntaxValid('Go cross compile', `
task cross-go
  describe Go cross compilation
  env GOOS=windows GOARCH=amd64
  go_build -o app.exe
end
`);

    await tester.testSyntaxValid('CMake cross compile', `
task cross-cmake
  describe CMake cross compilation
  cmake -DCMAKE_TOOLCHAIN_FILE=toolchain.cmake -B build-arm
  shell cmake --build build-arm
end
`);

    // Print summary
    console.log('\n=============================');
    console.log('📊 Build Helper Test Results');
    console.log('=============================');
    console.log(`✅ Passed: ${tester.passed}`);
    console.log(`❌ Failed: ${tester.failed}`);
    console.log(`📈 Success Rate: ${Math.round((tester.passed / (tester.passed + tester.failed)) * 100)}%`);

    if (tester.failed === 0) {
        console.log('\n🎉 All build helper tests passed!');
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

export { runTests, BuildHelperTester };
