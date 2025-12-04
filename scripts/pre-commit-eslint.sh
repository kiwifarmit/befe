#!/bin/bash
# ESLint hook for pre-commit
# Runs ESLint in Docker container for changed frontend files

set -e

# Get the project root (parent of scripts directory)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Change to project root
cd "$PROJECT_ROOT"

# Get changed files from pre-commit
CHANGED_FILES="$@"

# Filter only frontend JS/Vue files
FRONTEND_FILES=$(echo "$CHANGED_FILES" | grep -E '^frontend/.*\.(js|vue)$' || true)

if [ -z "$FRONTEND_FILES" ]; then
    # No frontend files changed, skip
    exit 0
fi

# Run ESLint in Docker container
# Note: We lint all frontend files, not just changed ones, to catch cross-file issues
# Exit code 1 means errors found, which pre-commit will treat as failure
docker-compose exec -T frontend npm run lint || exit 1
