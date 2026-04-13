#!/bin/bash
set -e

echo "Running type hint checks..."

# Check for missing type hints in production code
echo "1. Ruff ANN checks (production code only)..."
ruff check apps/ --select ANN --exclude "tests/,test_*.py,migrations/,admin.py"

# Optional: Run pyright for deeper type checking
echo "2. Pyright type checking..."
pyright apps/ --warnings

echo "✅ All type checks passed!"
