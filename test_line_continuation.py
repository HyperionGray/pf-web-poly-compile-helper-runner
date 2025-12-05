#!/usr/bin/env python3
"""
Test script to verify backslash line continuation functionality
"""

import sys
import os

# Add pf-runner to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'pf-runner'))

from pf_parser import parse_pfyfile_text

def test_line_continuation():
    """Test the backslash line continuation feature"""
    
    # Test case 1: Simple continuation
    test_pf_1 = """
task test-simple
  shell echo "line 1" \\
        && echo "line 2"
end
"""
    
    # Test case 2: Multi-line continuation (like docker example)
    test_pf_2 = """
task test-docker
  shell docker run --rm \\
          -v $(pwd):/app \\
          -w /app \\
          -p 8080:8080 \\
          myimage:latest
end
"""
    
    # Test case 3: Mixed continuation and regular lines
    test_pf_3 = """
task test-mixed
  shell echo "regular line"
  shell echo "continuation 1" \\
        && echo "continuation 2"
  shell echo "another regular line"
end
"""
    
    print("Testing backslash line continuation...")
    
    # Test 1
    print("\n=== Test 1: Simple continuation ===")
    tasks_1 = parse_pfyfile_text(test_pf_1)
    task_1 = tasks_1['test-simple']
    print(f"Number of lines in task: {len(task_1.lines)}")
    for i, line in enumerate(task_1.lines):
        print(f"Line {i+1}: {line}")
    
    # Test 2
    print("\n=== Test 2: Docker-style multi-line ===")
    tasks_2 = parse_pfyfile_text(test_pf_2)
    task_2 = tasks_2['test-docker']
    print(f"Number of lines in task: {len(task_2.lines)}")
    for i, line in enumerate(task_2.lines):
        print(f"Line {i+1}: {line}")
    
    # Test 3
    print("\n=== Test 3: Mixed lines ===")
    tasks_3 = parse_pfyfile_text(test_pf_3)
    task_3 = tasks_3['test-mixed']
    print(f"Number of lines in task: {len(task_3.lines)}")
    for i, line in enumerate(task_3.lines):
        print(f"Line {i+1}: {line}")
    
    # Verify expected behavior
    print("\n=== Verification ===")
    
    # Test 1 should have 1 line (continuation combined)
    expected_1 = 'shell echo "line 1" && echo "line 2"'
    actual_1 = task_1.lines[0]
    print(f"Test 1 - Expected: {expected_1}")
    print(f"Test 1 - Actual:   {actual_1}")
    print(f"Test 1 - Match: {expected_1 == actual_1}")
    
    # Test 2 should have 1 line (all docker args combined)
    expected_2 = 'shell docker run --rm -v $(pwd):/app -w /app -p 8080:8080 myimage:latest'
    actual_2 = task_2.lines[0]
    print(f"Test 2 - Expected: {expected_2}")
    print(f"Test 2 - Actual:   {actual_2}")
    print(f"Test 2 - Match: {expected_2 == actual_2}")
    
    # Test 3 should have 3 lines (regular, continuation, regular)
    expected_3_count = 3
    actual_3_count = len(task_3.lines)
    print(f"Test 3 - Expected line count: {expected_3_count}")
    print(f"Test 3 - Actual line count:   {actual_3_count}")
    print(f"Test 3 - Count match: {expected_3_count == actual_3_count}")
    
    if expected_3_count == actual_3_count:
        expected_3_line2 = 'shell echo "continuation 1" && echo "continuation 2"'
        actual_3_line2 = task_3.lines[1]
        print(f"Test 3 Line 2 - Expected: {expected_3_line2}")
        print(f"Test 3 Line 2 - Actual:   {actual_3_line2}")
        print(f"Test 3 Line 2 - Match: {expected_3_line2 == actual_3_line2}")

if __name__ == "__main__":
    test_line_continuation()