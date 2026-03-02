#!/bin/bash
# test_params.sh - Test script for parameter parsing
set -e

echo "=== Testing parameter parsing ==="
echo

PFY_FILE=test_params.pf
export PFY_FILE

echo "Test 1: Task without parameters"
./pf test-no-params
echo

echo "Test 2: Single parameter with default"
./pf test-single-param
echo

echo "Test 3: Single parameter with override"
./pf test-single-param x=20
echo

echo "Test 4: Multiple parameters with defaults"
./pf test-multiple-params
echo

echo "Test 5: Multiple parameters with partial override"
./pf test-multiple-params p2=SECOND
echo

echo "Test 6: Multiple parameters with full override"
./pf test-multiple-params p1=ONE p2=TWO p3=THREE
echo

echo "Test 7: Empty default value"
./pf test-empty-default
echo

echo "Test 8: Empty default with override"
./pf test-empty-default val=populated
echo

echo "Test 9: Hyphenated parameters with defaults"
./pf test-hyphenated-param
echo

echo "Test 10: Hyphenated parameters with override"
./pf test-hyphenated-param remote-addr=192.168.1.1 port=9090
echo

echo "Test 11: Hyphenated parameters with -- prefix"
./pf test-hyphenated-param --remote-addr=192.168.1.1 --port=9090
echo

echo "Test 12: Quoted default values"
./pf test-quoted-default
echo

echo "Test 13: Quoted default values with override"
./pf test-quoted-default msg="Custom Message" path=/custom/path
echo

echo "Test 14: Parameter interpolation in env"
./pf test-param-interpolation
echo

echo "Test 15: Parameter interpolation with override"
./pf test-param-interpolation base=/var subdir=cache
echo

echo "Test 16: Override only one parameter"
./pf test-override-one p1=custom1
echo

echo "Test 17: Special characters in defaults"
./pf test-special-chars
echo

echo "Test 18: Special characters with override"
./pf test-special-chars url="https://api.example.com/v2" name="prod-app-v2.1"
echo

echo "Test 19: Numeric parameters with defaults"
./pf test-numeric-params
echo

echo "Test 20: Numeric parameters with override"
./pf test-numeric-params count=500 timeout=60
echo

echo "=== All tests passed ==="
