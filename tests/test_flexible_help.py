#!/usr/bin/env python3
"""
Test script for flexible help options
"""

def _normalize_help_option(arg: str) -> bool:
    """Check if an argument is a help option, including common typos."""
    help_variations = {
        'help', '--help', '-h', 'hlep', 'hepl', 'heelp', 'hlp',
        '--hlep', '--hepl', '--heelp', '--hlp'
    }
    return arg.lower() in help_variations

# Test the function
test_cases = [
    'help', '--help', '-h', 'hlep', 'hepl', 'heelp', 'hlp',
    '--hlep', '--hepl', '--heelp', '--hlp', 'HELP', 'Help',
    'invalid', '--invalid', 'list'
]

print("Testing flexible help option detection:")
for case in test_cases:
    result = _normalize_help_option(case)
    print(f"  {case:12} -> {result}")