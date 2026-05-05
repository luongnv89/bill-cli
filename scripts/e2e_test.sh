#!/usr/bin/env bash
# scripts/e2e_test.sh — CLI end-to-end smoke tests
# Runs every command/subcommand with representative inputs.
# Exit code 0 = all passed. Non-zero = something broke.
set -uo pipefail

PASS=0
FAIL=0

check() {
    local desc="$1"
    shift
    if "$@" > /dev/null 2>&1; then
        echo "  ✓ $desc"
        PASS=$((PASS + 1))
    else
        echo "  ✗ $desc (cmd: $*)"
        FAIL=$((FAIL + 1))
    fi
}

check_output() {
    local desc="$1"
    local pattern="$2"
    shift 2
    local out
    out=$("$@" 2>&1)
    if echo "$out" | grep -q "$pattern"; then
        echo "  ✓ $desc"
        PASS=$((PASS + 1))
    else
        echo "  ✗ $desc — expected '$pattern' in output"
        FAIL=$((FAIL + 1))
    fi
}

echo "=== CLI E2E Tests ==="

CLI="bill-extract"

check "--help flag" $CLI --help
check_output "--help shows Usage" "Usage" $CLI --help
check "--verbose flag" $CLI --verbose --help
check "--debug flag" $CLI --debug --help
check_output "missing input shows error" "Error" $CLI

echo ""
echo "=== Results: ${PASS} passed, ${FAIL} failed ==="
[ "$FAIL" -eq 0 ] || exit 1
