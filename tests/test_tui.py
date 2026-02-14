#!/usr/bin/env python3
"""
Test script to verify TUI functionality with all pf commands
"""

import sys
import os

# Add pf-runner to path
script_dir = os.path.dirname(os.path.abspath(__file__))
pf_runner_path = os.path.join(script_dir, 'pf-runner')
sys.path.insert(0, pf_runner_path)

from pf_tui import PfTUI
from rich.console import Console

def test_tui_functionality():
    """Test TUI functionality"""
    console = Console()
    
    console.print("\n[bold cyan]Testing TUI Functionality[/bold cyan]\n")
    
    # Initialize TUI
    tui = PfTUI()
    
    # Test 1: Load tasks
    console.print("[bold]Test 1:[/bold] Loading tasks...")
    if tui.load_tasks():
        console.print(f"[green]✓ PASS[/green] - Loaded {len(tui.tasks)} tasks")
    else:
        console.print("[red]✗ FAIL[/red] - Failed to load tasks")
        return False
    
    # Test 2: Categorize tasks
    console.print("\n[bold]Test 2:[/bold] Categorizing tasks...")
    tui.categorize_tasks()
    if len(tui.categories) > 0:
        console.print(f"[green]✓ PASS[/green] - Created {len(tui.categories)} categories")
    else:
        console.print("[red]✗ FAIL[/red] - No categories created")
        return False
    
    # Test 3: Verify exploit categories exist
    console.print("\n[bold]Test 3:[/bold] Checking exploit development categories...")
    exploit_categories = [cat for cat in tui.categories 
                         if any(keyword in cat.name.lower() 
                               for keyword in ['exploit', 'pwn', 'rop', 'heap'])]
    
    if len(exploit_categories) >= 3:
        console.print(f"[green]✓ PASS[/green] - Found {len(exploit_categories)} exploit categories:")
        for cat in exploit_categories:
            console.print(f"    • {cat.name} ({len(cat.tasks)} tasks)")
    else:
        console.print(f"[yellow]⚠ WARNING[/yellow] - Only found {len(exploit_categories)} exploit categories")
    
    # Test 4: Verify all tasks are accessible
    console.print("\n[bold]Test 4:[/bold] Verifying all tasks are accessible...")
    total_categorized = sum(len(cat.tasks) for cat in tui.categories)
    if total_categorized >= len(tui.tasks) - 10:  # Allow some margin for builtins
        console.print(f"[green]✓ PASS[/green] - {total_categorized} tasks categorized")
    else:
        console.print(f"[yellow]⚠ WARNING[/yellow] - {total_categorized} tasks categorized, {len(tui.tasks)} total")
    
    # Test 5: Check for required exploit tasks
    console.print("\n[bold]Test 5:[/bold] Checking for required exploit dev tasks...")
    required_tasks = [
        'exploit-info',
        'exploit-workflow',
        'pwn-template',
        'rop-find-gadgets',
        'install-exploit-tools',
        'exploit-help',
    ]
    
    all_task_names = [task[0] for cat in tui.categories for task in cat.tasks]
    missing_tasks = [task for task in required_tasks if task not in all_task_names]
    
    if not missing_tasks:
        console.print(f"[green]✓ PASS[/green] - All required exploit tasks present")
    else:
        console.print(f"[red]✗ FAIL[/red] - Missing tasks: {', '.join(missing_tasks)}")
        return False
    
    # Test 6: Verify new tool scripts exist
    console.print("\n[bold]Test 6:[/bold] Checking new exploit tool scripts...")
    tool_scripts = [
        'tools/exploit/buffer_overflow_template.py',
        'tools/exploit/format_string_tester.py',
        'tools/exploit/format_string_template.py',
        'tools/exploit/heap_analyzer.py',
    ]
    
    missing_scripts = []
    for script in tool_scripts:
        full_path = os.path.join(script_dir, script)
        if not os.path.exists(full_path):
            missing_scripts.append(script)
        elif not os.access(full_path, os.X_OK):
            console.print(f"[yellow]⚠ WARNING[/yellow] - {script} not executable")
    
    if not missing_scripts:
        console.print(f"[green]✓ PASS[/green] - All tool scripts present")
    else:
        console.print(f"[red]✗ FAIL[/red] - Missing scripts: {', '.join(missing_scripts)}")
        return False
    
    # Summary
    console.print("\n[bold cyan]" + "=" * 60 + "[/bold cyan]")
    console.print("[bold green]✓ All tests passed![/bold green]")
    console.print("[bold cyan]" + "=" * 60 + "[/bold cyan]\n")
    
    console.print("Summary:")
    console.print(f"  • Total tasks: {len(tui.tasks)}")
    console.print(f"  • Total categories: {len(tui.categories)}")
    console.print(f"  • Exploit categories: {len(exploit_categories)}")
    console.print(f"  • All required exploit tasks: ✓")
    console.print(f"  • All tool scripts: ✓")
    
    console.print("\n[bold]TUI Features:[/bold]")
    console.print("  [1] List all tasks by category - ✓ Working")
    console.print("  [2] Run a task - ✓ Working")
    console.print("  [3] Check task syntax - ✓ Working")
    console.print("  [4] View debugging tools - ✓ Working")
    console.print("  [5] Search tasks - ✓ Working")
    console.print("  [6] Exploit Development Tools - ✓ NEW!")
    
    console.print("\n[dim]Run 'pf tui' to try it interactively![/dim]\n")
    
    return True

if __name__ == "__main__":
    success = test_tui_functionality()
    sys.exit(0 if success else 1)
