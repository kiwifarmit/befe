#!/bin/bash
# Setup script for pre-commit hooks
# This script sets up pre-commit using the project's dedicated virtual environment

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
VENV_PATH="$PROJECT_ROOT/venv"

echo "Setting up pre-commit hooks..."
echo "Project root: $PROJECT_ROOT"
echo ""

# Check if venv exists
if [ ! -d "$VENV_PATH" ]; then
    echo "Creating virtual environment..."
    python3 -m venv "$VENV_PATH"
    echo "✅ Virtual environment created"
fi

# Activate venv and install pre-commit
echo "Activating virtual environment..."
source "$VENV_PATH/bin/activate"

echo "Upgrading pip..."
pip install --upgrade pip --quiet

echo "Installing pre-commit..."
pip install pre-commit --quiet

# Install pre-commit hooks
echo "Installing pre-commit git hooks..."
pre-commit install

echo ""
echo "✅ Pre-commit hooks installed successfully!"
echo ""
echo "The virtual environment is located at: $VENV_PATH"
echo ""
echo "To use pre-commit in the future:"
echo "  source venv/bin/activate"
echo "  pre-commit run --all-files"
echo ""
echo "Or the hooks will run automatically on 'git commit'"
echo ""
