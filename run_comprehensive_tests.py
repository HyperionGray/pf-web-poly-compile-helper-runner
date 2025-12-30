#!/usr/bin/env python3
"""
Comprehensive Test Runner for pf-web-poly-compile-helper-runner

This script runs all tests and generates comprehensive coverage reports:
- Python unit tests with coverage
- JavaScript/Node.js tests
- Playwright E2E tests
- Security scans
- Code quality checks
- Performance benchmarks

Usage:
    python run_comprehensive_tests.py [options]
    
Options:
    --python-only    Run only Python tests
    --js-only        Run only JavaScript tests
    --e2e-only       Run only E2E tests
    --security-only  Run only security scans
    --coverage       Generate coverage reports
    --verbose        Verbose output
    --fast           Skip slow tests
"""

import os
import sys
import subprocess
import argparse
import json
import time
from pathlib import Path
from typing import Dict, List, Tuple, Optional


class TestRunner:
    """Comprehensive test runner for the project"""
    
    def __init__(self, verbose: bool = False, fast: bool = False):
        self.verbose = verbose
        self.fast = fast
        self.results = {}
        self.start_time = time.time()
        
        # Project paths
        self.root_dir = Path(__file__).parent
        self.pf_runner_dir = self.root_dir / "pf-runner"
        self.tests_dir = self.root_dir / "tests"
        
    def log(self, message: str, level: str = "INFO"):
        """Log message with timestamp"""
        timestamp = time.strftime("%H:%M:%S")
        if self.verbose or level in ["ERROR", "SUCCESS"]:
            print(f"[{timestamp}] {level}: {message}")
    
    def run_command(self, cmd: List[str], cwd: Optional[Path] = None, 
                   capture_output: bool = True) -> Tuple[int, str, str]:
        """Run command and return exit code, stdout, stderr"""
        if cwd is None:
            cwd = self.root_dir
            
        self.log(f"Running: {' '.join(cmd)}", "DEBUG")
        
        try:
            result = subprocess.run(
                cmd, 
                cwd=cwd, 
                capture_output=capture_output,
                text=True,
                timeout=300 if not self.fast else 60
            )
            return result.returncode, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            self.log(f"Command timed out: {' '.join(cmd)}", "ERROR")
            return 1, "", "Command timed out"
        except Exception as e:
            self.log(f"Command failed: {e}", "ERROR")
            return 1, "", str(e)
    
    def check_dependencies(self) -> bool:
        """Check if required dependencies are installed"""
        self.log("Checking dependencies...")
        
        dependencies = [
            (["python", "--version"], "Python"),
            (["node", "--version"], "Node.js"),
            (["npm", "--version"], "npm"),
        ]
        
        missing = []
        for cmd, name in dependencies:
            code, _, _ = self.run_command(cmd)
            if code != 0:
                missing.append(name)
        
        if missing:
            self.log(f"Missing dependencies: {', '.join(missing)}", "ERROR")
            return False
        
        self.log("All dependencies available", "SUCCESS")
        return True
    
    def install_python_deps(self) -> bool:
        """Install Python dependencies"""
        self.log("Installing Python dependencies...")
        
        deps = [
            "fabric>=3.2,<4",
            "rich",
            "lark",
            "pytest",
            "coverage",
            "pytest-cov",
            "black",
            "flake8",
            "pylint",
            "bandit",
            "safety"
        ]
        
        for dep in deps:
            code, _, stderr = self.run_command(["pip", "install", dep])
            if code != 0:
                self.log(f"Failed to install {dep}: {stderr}", "ERROR")
                return False
        
        self.log("Python dependencies installed", "SUCCESS")
        return True
    
    def install_node_deps(self) -> bool:
        """Install Node.js dependencies"""
        self.log("Installing Node.js dependencies...")
        
        code, _, stderr = self.run_command(["npm", "ci"])
        if code != 0:
            self.log(f"Failed to install Node.js dependencies: {stderr}", "ERROR")
            return False
        
        self.log("Node.js dependencies installed", "SUCCESS")
        return True
    
    def run_python_tests(self) -> bool:
        """Run Python unit tests with coverage"""
        self.log("Running Python tests...")
        
        # Run pytest with coverage
        cmd = [
            "python", "-m", "pytest",
            str(self.tests_dir),
            "--cov=pf-runner",
            "--cov-report=term-missing",
            "--cov-report=html:htmlcov",
            "--cov-report=xml:coverage.xml",
            "--verbose" if self.verbose else "--quiet",
        ]
        
        if self.fast:
            cmd.extend(["-m", "not slow"])
        
        code, stdout, stderr = self.run_command(cmd)
        
        self.results["python_tests"] = {
            "exit_code": code,
            "passed": code == 0,
            "output": stdout,
            "errors": stderr
        }
        
        if code == 0:
            self.log("Python tests passed", "SUCCESS")
        else:
            self.log(f"Python tests failed: {stderr}", "ERROR")
        
        return code == 0
    
    def run_javascript_tests(self) -> bool:
        """Run JavaScript/Node.js tests"""
        self.log("Running JavaScript tests...")
        
        test_commands = [
            (["npm", "run", "test:unit"], "Unit tests"),
            (["npm", "run", "test:grammar"], "Grammar tests"),
            (["npm", "run", "test:tui"], "TUI tests"),
            (["npm", "run", "test:api"], "API tests"),
        ]
        
        all_passed = True
        for cmd, name in test_commands:
            self.log(f"Running {name}...")
            code, stdout, stderr = self.run_command(cmd)
            
            self.results[f"js_{name.lower().replace(' ', '_')}"] = {
                "exit_code": code,
                "passed": code == 0,
                "output": stdout,
                "errors": stderr
            }
            
            if code == 0:
                self.log(f"{name} passed", "SUCCESS")
            else:
                self.log(f"{name} failed: {stderr}", "ERROR")
                all_passed = False
        
        return all_passed
    
    def run_e2e_tests(self) -> bool:
        """Run Playwright E2E tests"""
        self.log("Running E2E tests...")
        
        # Install Playwright browsers if needed
        code, _, _ = self.run_command(["npx", "playwright", "install", "--with-deps"])
        if code != 0:
            self.log("Failed to install Playwright browsers", "ERROR")
        
        # Run Playwright tests
        cmd = ["npm", "run", "test"]
        if self.fast:
            cmd.extend(["--", "--workers=1"])
        
        code, stdout, stderr = self.run_command(cmd)
        
        self.results["e2e_tests"] = {
            "exit_code": code,
            "passed": code == 0,
            "output": stdout,
            "errors": stderr
        }
        
        if code == 0:
            self.log("E2E tests passed", "SUCCESS")
        else:
            self.log(f"E2E tests failed: {stderr}", "ERROR")
        
        return code == 0
    
    def run_security_scans(self) -> bool:
        """Run security scans"""
        self.log("Running security scans...")
        
        security_commands = [
            (["npm", "run", "security:scan"], "Credential scan"),
            (["npm", "run", "security:deps"], "Dependency scan"),
            (["python", "-m", "bandit", "-r", "pf-runner/", "-f", "json"], "Python security scan"),
            (["python", "-m", "safety", "check", "--json"], "Python dependency scan"),
        ]
        
        all_passed = True
        for cmd, name in security_commands:
            self.log(f"Running {name}...")
            code, stdout, stderr = self.run_command(cmd)
            
            # Security scans may return non-zero for findings, which is not necessarily a failure
            passed = code == 0 or "No issues found" in stdout or "No vulnerabilities found" in stdout
            
            self.results[f"security_{name.lower().replace(' ', '_')}"] = {
                "exit_code": code,
                "passed": passed,
                "output": stdout,
                "errors": stderr
            }
            
            if passed:
                self.log(f"{name} completed successfully", "SUCCESS")
            else:
                self.log(f"{name} found issues: {stderr}", "ERROR")
                all_passed = False
        
        return all_passed
    
    def run_code_quality_checks(self) -> bool:
        """Run code quality checks"""
        self.log("Running code quality checks...")
        
        quality_commands = [
            (["python", "-m", "black", "--check", "--diff", "pf-runner/"], "Python formatting"),
            (["python", "-m", "flake8", "pf-runner/", "--max-line-length=120"], "Python linting"),
            (["npx", "eslint", "tools/", "tests/", "--ext", ".js,.mjs,.ts"], "JavaScript linting"),
        ]
        
        all_passed = True
        for cmd, name in quality_commands:
            self.log(f"Running {name}...")
            code, stdout, stderr = self.run_command(cmd)
            
            self.results[f"quality_{name.lower().replace(' ', '_')}"] = {
                "exit_code": code,
                "passed": code == 0,
                "output": stdout,
                "errors": stderr
            }
            
            if code == 0:
                self.log(f"{name} passed", "SUCCESS")
            else:
                self.log(f"{name} failed: {stderr}", "ERROR")
                all_passed = False
        
        return all_passed
    
    def run_performance_tests(self) -> bool:
        """Run performance benchmarks"""
        if self.fast:
            self.log("Skipping performance tests in fast mode")
            return True
        
        self.log("Running performance tests...")
        
        # Basic performance test for parser
        perf_script = """
import sys
import os
import time
sys.path.insert(0, 'pf-runner')

try:
    import pf_parser
    
    # Create test file
    with open('perf_test.pf', 'w') as f:
        for i in range(50):
            f.write(f'''
task test_{i}:
    describe "Test task {i}"
    shell echo "Task {i}"
''')
    
    # Benchmark parsing
    start = time.time()
    for _ in range(10):
        tasks = pf_parser.parse_pfyfile('perf_test.pf')
    end = time.time()
    
    avg_time = (end - start) / 10 * 1000
    print(f"Average parse time: {avg_time:.2f}ms")
    
    # Cleanup
    os.remove('perf_test.pf')
    
    # Performance threshold: should be under 100ms
    if avg_time < 100:
        print("PASS: Performance within acceptable limits")
        exit(0)
    else:
        print("FAIL: Performance too slow")
        exit(1)
        
except Exception as e:
    print(f"Performance test failed: {e}")
    exit(1)
"""
        
        with open(self.root_dir / "perf_test.py", "w") as f:
            f.write(perf_script)
        
        code, stdout, stderr = self.run_command(["python", "perf_test.py"])
        
        # Cleanup
        perf_file = self.root_dir / "perf_test.py"
        if perf_file.exists():
            perf_file.unlink()
        
        self.results["performance_tests"] = {
            "exit_code": code,
            "passed": code == 0,
            "output": stdout,
            "errors": stderr
        }
        
        if code == 0:
            self.log("Performance tests passed", "SUCCESS")
        else:
            self.log(f"Performance tests failed: {stderr}", "ERROR")
        
        return code == 0
    
    def generate_report(self) -> None:
        """Generate comprehensive test report"""
        self.log("Generating test report...")
        
        total_time = time.time() - self.start_time
        
        report = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
            "total_duration": f"{total_time:.2f}s",
            "summary": {
                "total_tests": len(self.results),
                "passed": sum(1 for r in self.results.values() if r.get("passed", False)),
                "failed": sum(1 for r in self.results.values() if not r.get("passed", True)),
            },
            "results": self.results
        }
        
        # Write JSON report
        with open(self.root_dir / "test_report.json", "w") as f:
            json.dump(report, f, indent=2)
        
        # Write markdown report
        md_report = f"""# Test Report - {report['timestamp']}

## Summary
- **Total Duration**: {report['total_duration']}
- **Total Tests**: {report['summary']['total_tests']}
- **Passed**: {report['summary']['passed']}
- **Failed**: {report['summary']['failed']}

## Results

"""
        
        for test_name, result in self.results.items():
            status = "✅ PASS" if result.get("passed", False) else "❌ FAIL"
            md_report += f"### {test_name.replace('_', ' ').title()}\n"
            md_report += f"**Status**: {status}\n"
            md_report += f"**Exit Code**: {result.get('exit_code', 'N/A')}\n"
            if result.get("errors"):
                md_report += f"**Errors**: {result['errors'][:200]}...\n"
            md_report += "\n"
        
        with open(self.root_dir / "TEST_REPORT.md", "w") as f:
            f.write(md_report)
        
        self.log(f"Test report generated: {report['summary']['passed']}/{report['summary']['total_tests']} passed", "SUCCESS")
    
    def run_all_tests(self, python_only=False, js_only=False, e2e_only=False, security_only=False) -> bool:
        """Run all tests based on options"""
        if not self.check_dependencies():
            return False
        
        success = True
        
        if not (js_only or e2e_only or security_only):
            if not self.install_python_deps():
                return False
            success &= self.run_python_tests()
            success &= self.run_code_quality_checks()
            success &= self.run_performance_tests()
        
        if not (python_only or e2e_only or security_only):
            if not self.install_node_deps():
                return False
            success &= self.run_javascript_tests()
        
        if not (python_only or js_only or security_only):
            if not self.install_node_deps():
                return False
            success &= self.run_e2e_tests()
        
        if not (python_only or js_only or e2e_only):
            success &= self.run_security_scans()
        
        self.generate_report()
        return success


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Comprehensive test runner")
    parser.add_argument("--python-only", action="store_true", help="Run only Python tests")
    parser.add_argument("--js-only", action="store_true", help="Run only JavaScript tests")
    parser.add_argument("--e2e-only", action="store_true", help="Run only E2E tests")
    parser.add_argument("--security-only", action="store_true", help="Run only security scans")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--fast", action="store_true", help="Skip slow tests")
    
    args = parser.parse_args()
    
    runner = TestRunner(verbose=args.verbose, fast=args.fast)
    
    success = runner.run_all_tests(
        python_only=args.python_only,
        js_only=args.js_only,
        e2e_only=args.e2e_only,
        security_only=args.security_only
    )
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()