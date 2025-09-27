#!/bin/bash

# =============================================================================
# NEURON QUICK CHECK SCRIPT
# =============================================================================
# Quick version that runs only the essential checks (linting, formatting, type-check)
# This is faster than the full check-local.sh script
#
# Usage: ./quick-check.sh
# =============================================================================

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to run a step with error handling
run_step() {
    local step_name="$1"
    shift
    local command=("$@")

    print_status "Running: $step_name"

    if "${command[@]}"; then
        print_success "$step_name completed successfully"
        return 0
    else
        print_error "$step_name failed"
        return 1
    fi
}

# Main execution
main() {
    echo "============================================================================="
    echo "NEURON QUICK CHECK SCRIPT"
    echo "============================================================================="
    echo "Running essential checks: linting, formatting, and type checking"
    echo "============================================================================="
    echo ""

    # Change to project root directory (where the script is located)
    SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
    cd "$SCRIPT_DIR"
    print_status "Working directory: $(pwd)"
    echo ""

    # Frontend checks
    print_status "Starting frontend checks..."
    echo ""

    # Step 1: Run frontend linting
    if ! run_step "Run frontend linting" bash -c "cd frontend && yarn lint"; then
        print_error "Frontend linting failed"
        exit 1
    fi
    echo ""

    # Step 2: Run frontend formatting check
    if ! run_step "Run frontend formatting" bash -c "cd frontend && yarn format"; then
        print_error "Frontend formatting failed"
        exit 1
    fi
    echo ""

    # Step 3: Run TypeScript type checking
    if ! run_step "Run TypeScript type checking" bash -c "cd frontend && yarn type-check"; then
        print_error "TypeScript type checking failed"
        exit 1
    fi
    echo ""

    print_success "All essential checks passed!"
    echo ""
    echo "============================================================================="
    print_success "QUICK CHECK COMPLETED SUCCESSFULLY!"
    echo "============================================================================="
    echo ""
    print_status "Summary of checks performed:"
    echo "  ✓ Frontend linting (ESLint)"
    echo "  ✓ Frontend code formatting (Prettier)"
    echo "  ✓ TypeScript type checking"
    echo ""
    print_success "Your code is ready for commit!"
    echo "============================================================================="
}

# Run the main function
main "$@"
