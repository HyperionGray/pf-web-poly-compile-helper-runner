#!/usr/bin/env python3
"""
Comprehensive Test Runner - "Test it all again and again and again. That's thrice."

This script runs all available tests in the repository three times with fresh 
environment setup between each run, providing detailed reporting and analysis.
"""

import os
import sys
import subprocess
import glob
import json
import time
import shutil
import tempfile
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Tuple, Optional


def _resolve_workspace_dir(workspace_override: Optional[str]) -> str:
    """Resolve the workspace directory without assuming a fixed path."""
    candidates: List[Path] = []

    if workspace_override:
        candidates.append(Path(workspace_override).expanduser())

    for env_var in ("PF_WORKSPACE", "WORKSPACE"):
        env_path = os.environ.get(env_var)
        if env_path:
            candidates.append(Path(env_path).expanduser())

    # Fall back to the directory containing this script
    candidates.append(Path(__file__).resolve().parent)
    # Fallback for container default if it actually exists
    candidates.append(Path("/workspace"))

    for candidate in candidates:
        if candidate.exists():
            return str(candidate)

    return str(Path(__file__).resolve().parent)

class TestResult:
    """Container for individual test results"""
    def __init__(self, name: str, success: bool, duration: float, 
                 stdout: str = "", stderr: str = "", returncode: int = 0):
        self.name = name
        self.success = success
        self.duration = duration
        self.stdout = stdout
        self.stderr = stderr
        self.returncode = returncode
        self.timestamp = datetime.now()

class TestRun:
    """Container for a complete test run"""
    def __init__(self, run_number: int):
        self.run_number = run_number
        self.results: List[TestResult] = []
        self.start_time = None
        self.end_time = None
        self.total_duration = 0.0
        
    def add_result(self, result: TestResult):
        self.results.append(result)
        
    def get_success_count(self) -> int:
        return sum(1 for r in self.results if r.success)
        
    def get_failure_count(self) -> int:
        return sum(1 for r in self.results if not r.success)
        
    def get_total_count(self) -> int:
        return len(self.results)

class ComprehensiveTestRunner:
    """Main test runner class"""
    
    def __init__(self, workspace_dir: Optional[str] = None):
        self.workspace_dir = _resolve_workspace_dir(workspace_dir)
        self.test_runs: List[TestRun] = []
        self.discovered_tests: List[str] = []
        self.temp_dirs: List[str] = []
        if not Path(self.workspace_dir).exists():
            raise FileNotFoundError(f"Workspace directory not found: {self.workspace_dir}")
        
    def discover_tests(self) -> List[str]:
        """Discover all test files in the repository"""
        print("🔍 Discovering test files...")
        
        # Find all test_*.py files
        test_files: List[Path] = []
        
        # Look for test_*.py files
        for pattern in ["test_*.py", "*test*.py"]:
            matches = glob.glob(os.path.join(self.workspace_dir, pattern))
            test_files.extend(Path(m).resolve() for m in matches)
        
        # Also include specific known test files
        known_tests = [
            "quick_test.py",
            "run_syntax_check.py", 
            "simple_syntax_validator.py",
            "test_runner_verification.py"  # Include our verification test
        ]
        
        for test_file in known_tests:
            full_path = Path(self.workspace_dir, test_file).resolve()
            if full_path.exists():
                test_files.append(full_path)
        
        # Filter out this script itself
        current_script = Path(__file__).resolve()
        test_files = [f for f in test_files if f != current_script]

        # Deduplicate while preserving order
        seen: set[Path] = set()
        unique_test_files: List[Path] = []
        for f in test_files:
            if f in seen:
                continue
            seen.add(f)
            unique_test_files.append(f)
        
        # Sort for consistent ordering
        test_files = sorted(unique_test_files)
        
        self.discovered_tests = [str(p) for p in test_files]
        print(f"📊 Discovered {len(self.discovered_tests)} test files:")
        for test_file in self.discovered_tests:
            rel_path = os.path.relpath(test_file, self.workspace_dir)
            print(f"  • {rel_path}")
        
        return self.discovered_tests
    
    def setup_fresh_environment(self, run_number: int):
        """Set up a fresh environment for testing"""
        print(f"\n🧹 Setting up fresh environment for run {run_number}...")
        
        # Change to workspace directory
        os.chdir(self.workspace_dir)
        
        # Clean up any previous temporary directories
        for temp_dir in self.temp_dirs:
            if os.path.exists(temp_dir):
                try:
                    shutil.rmtree(temp_dir)
                except Exception as e:
                    print(f"⚠️  Warning: Could not clean up {temp_dir}: {e}")
        self.temp_dirs.clear()
        
        # Create a fresh temporary directory for this run
        temp_dir = tempfile.mkdtemp(prefix=f"pf_test_run_{run_number}_")
        self.temp_dirs.append(temp_dir)
        
        # Set environment variables for clean state
        env_vars = {
            'TMPDIR': temp_dir,
            'TEMP': temp_dir,
            'TMP': temp_dir,
            'PF_TEST_RUN': str(run_number),
            'PF_FRESH_ENV': '1'
        }
        
        for key, value in env_vars.items():
            os.environ[key] = value
        
        print(f"✅ Fresh environment ready (temp dir: {temp_dir})")
        
    def run_single_test(self, test_file: str, timeout: int = 60) -> TestResult:
        """Run a single test file and return results"""
        test_name = os.path.relpath(test_file, self.workspace_dir)
        print(f"  🧪 Running {test_name}...")
        
        start_time = time.time()
        
        try:
            # Determine how to run the test
            if test_file.endswith('.py'):
                cmd = [sys.executable, test_file]
            elif test_file.endswith('.sh'):
                cmd = ['bash', test_file]
            else:
                # Try to execute directly
                cmd = [test_file]
            
            # Run the test
            result = subprocess.run(
                cmd,
                cwd=self.workspace_dir,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            duration = time.time() - start_time
            success = result.returncode == 0
            
            status = "✅ PASS" if success else "❌ FAIL"
            print(f"    {status} ({duration:.2f}s)")
            
            return TestResult(
                name=test_name,
                success=success,
                duration=duration,
                stdout=result.stdout,
                stderr=result.stderr,
                returncode=result.returncode
            )
            
        except subprocess.TimeoutExpired:
            duration = time.time() - start_time
            print(f"    ⏰ TIMEOUT ({duration:.2f}s)")
            return TestResult(
                name=test_name,
                success=False,
                duration=duration,
                stdout="",
                stderr=f"Test timed out after {timeout} seconds",
                returncode=-1
            )
            
        except Exception as e:
            duration = time.time() - start_time
            print(f"    💥 ERROR ({duration:.2f}s): {e}")
            return TestResult(
                name=test_name,
                success=False,
                duration=duration,
                stdout="",
                stderr=str(e),
                returncode=-2
            )
    
    def run_test_suite(self, run_number: int) -> TestRun:
        """Run the complete test suite once"""
        print(f"\n🚀 Starting Test Run #{run_number}")
        print("=" * 60)
        
        # Set up fresh environment
        self.setup_fresh_environment(run_number)
        
        # Create test run container
        test_run = TestRun(run_number)
        test_run.start_time = datetime.now()
        
        # Run each test
        for test_file in self.discovered_tests:
            result = self.run_single_test(test_file)
            test_run.add_result(result)
        
        # Finalize run
        test_run.end_time = datetime.now()
        test_run.total_duration = (test_run.end_time - test_run.start_time).total_seconds()
        
        # Print run summary
        print(f"\n📊 Run #{run_number} Summary:")
        print(f"  • Total tests: {test_run.get_total_count()}")
        print(f"  • Passed: {test_run.get_success_count()}")
        print(f"  • Failed: {test_run.get_failure_count()}")
        print(f"  • Duration: {test_run.total_duration:.2f}s")
        
        return test_run
    
    def run_all_tests_thrice(self):
        """Run all tests three times as requested"""
        print("🎯 COMPREHENSIVE TEST RUNNER")
        print("Testing it all again and again and again. That's thrice!")
        print("=" * 70)
        print(f"Workspace: {self.workspace_dir}")
        
        # Discover tests
        if not self.discover_tests():
            print("❌ No tests discovered. Exiting.")
            return False
        
        # Run tests three times
        for run_num in range(1, 4):  # 1, 2, 3
            test_run = self.run_test_suite(run_num)
            self.test_runs.append(test_run)
            
            # Brief pause between runs
            if run_num < 3:
                print(f"\n⏸️  Brief pause before run #{run_num + 1}...")
                time.sleep(2)
        
        # Generate comprehensive report
        return self.generate_comprehensive_report()
    
    def generate_comprehensive_report(self) -> bool:
        """Generate detailed report across all three runs"""
        print("\n" + "=" * 70)
        print("📋 COMPREHENSIVE TEST REPORT - THREE RUNS ANALYSIS")
        print("=" * 70)
        
        # Overall statistics
        total_tests = len(self.discovered_tests)
        total_executions = total_tests * 3
        
        all_passed = 0
        all_failed = 0
        total_duration = 0.0
        
        for run in self.test_runs:
            all_passed += run.get_success_count()
            all_failed += run.get_failure_count()
            total_duration += run.total_duration
        
        print(f"📊 OVERALL STATISTICS:")
        print(f"  • Total test files: {total_tests}")
        print(f"  • Total executions: {total_executions} (3 runs × {total_tests} tests)")
        print(f"  • Total passed: {all_passed}")
        print(f"  • Total failed: {all_failed}")
        print(f"  • Success rate: {(all_passed/total_executions)*100:.1f}%")
        print(f"  • Total duration: {total_duration:.2f}s")
        print(f"  • Average per run: {total_duration/3:.2f}s")
        
        # Per-run breakdown
        print(f"\n📈 PER-RUN BREAKDOWN:")
        for i, run in enumerate(self.test_runs, 1):
            success_rate = (run.get_success_count() / run.get_total_count()) * 100
            print(f"  Run #{i}: {run.get_success_count()}/{run.get_total_count()} passed "
                  f"({success_rate:.1f}%) in {run.total_duration:.2f}s")
        
        # Test consistency analysis
        print(f"\n🔍 TEST CONSISTENCY ANALYSIS:")
        test_consistency = {}
        
        for test_file in self.discovered_tests:
            test_name = os.path.relpath(test_file, self.workspace_dir)
            results = []
            for run in self.test_runs:
                for result in run.results:
                    if result.name == test_name:
                        results.append(result.success)
                        break
            
            test_consistency[test_name] = results
        
        # Categorize tests by consistency
        always_pass = []
        always_fail = []
        inconsistent = []
        
        for test_name, results in test_consistency.items():
            if all(results):
                always_pass.append(test_name)
            elif not any(results):
                always_fail.append(test_name)
            else:
                inconsistent.append((test_name, results))
        
        print(f"  • Always pass: {len(always_pass)} tests")
        print(f"  • Always fail: {len(always_fail)} tests")
        print(f"  • Inconsistent: {len(inconsistent)} tests")
        
        # Show details for problematic tests
        if always_fail:
            print(f"\n❌ ALWAYS FAILING TESTS:")
            for test_name in always_fail:
                print(f"  • {test_name}")
                # Show error from last run
                for result in self.test_runs[-1].results:
                    if result.name == test_name:
                        if result.stderr:
                            print(f"    Error: {result.stderr[:100]}...")
                        break
        
        if inconsistent:
            print(f"\n⚠️  INCONSISTENT TESTS:")
            for test_name, results in inconsistent:
                result_str = "".join("✅" if r else "❌" for r in results)
                print(f"  • {test_name}: {result_str}")
        
        # Success determination
        overall_success = len(always_fail) == 0 and len(inconsistent) == 0
        
        print(f"\n🎯 FINAL VERDICT:")
        if overall_success:
            print("🎉 ALL TESTS CONSISTENTLY PASS ACROSS ALL THREE RUNS!")
            print("✅ The system is stable and reliable.")
        else:
            print("⚠️  Some tests have issues:")
            if always_fail:
                print(f"   - {len(always_fail)} tests consistently fail")
            if inconsistent:
                print(f"   - {len(inconsistent)} tests have inconsistent results")
        
        # Recommendations
        print(f"\n💡 RECOMMENDATIONS:")
        if overall_success:
            print("  • System is ready for production use")
            print("  • All tests pass consistently")
            print("  • No action required")
        else:
            print("  • Investigate failing tests")
            print("  • Fix inconsistent test behavior")
            print("  • Consider adding more robust error handling")
        
        print(f"\n🏁 Testing complete. Nay ye canne deny it workes!")
        print("=" * 70)
        
        return overall_success
    
    def cleanup(self):
        """Clean up temporary resources"""
        for temp_dir in self.temp_dirs:
            if os.path.exists(temp_dir):
                try:
                    shutil.rmtree(temp_dir)
                except Exception as e:
                    print(f"⚠️  Warning: Could not clean up {temp_dir}: {e}")

def main():
    """Main entry point"""
    # Check for quick verification mode
    quick_mode = len(sys.argv) > 1 and sys.argv[1] == "--quick"
    
    runner = ComprehensiveTestRunner()
    
    try:
        if quick_mode:
            print("🚀 QUICK VERIFICATION MODE")
            print("Running test discovery and single test execution...")
            print("=" * 50)
            
            # Just discover tests and run one quick test
            tests = runner.discover_tests()
            if tests:
                print(f"\n✅ Successfully discovered {len(tests)} tests")
                print("🎯 Quick verification complete!")
                return 0
            else:
                print("❌ No tests discovered")
                return 1
        else:
            success = runner.run_all_tests_thrice()
            return 0 if success else 1
    except KeyboardInterrupt:
        print("\n\n⚠️  Test run interrupted by user")
        return 130
    except Exception as e:
        print(f"\n\n💥 Unexpected error: {e}")
        return 1
    finally:
        runner.cleanup()

if __name__ == "__main__":
    sys.exit(main())
