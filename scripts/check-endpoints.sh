#!/bin/bash
# Pre-commit hook to ensure update_user_credits endpoint is not removed
# This script checks that the endpoint exists before allowing commit
# CRITICAL: This endpoint must not be removed - it's required for admin credit management

set -euo pipefail

# Get the project root (assuming script is in scripts/)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
# Check both possible locations
ENDPOINTS_FILE="$PROJECT_ROOT/backend/app/api/endpoints.py"
CREDITS_FILE="$PROJECT_ROOT/backend/app/api/credits.py"

# If pre-commit passes files, use the first one, otherwise use the default
if [ $# -gt 0 ] && [ -f "$1" ]; then
    if [[ "$1" == *"credits.py" ]]; then
        CREDITS_FILE="$1"
    else
        ENDPOINTS_FILE="$1"
    fi
fi

# Check if credits.py exists (preferred location)
if [ -f "$CREDITS_FILE" ]; then
    CHECK_FILE="$CREDITS_FILE"
elif [ -f "$ENDPOINTS_FILE" ]; then
    CHECK_FILE="$ENDPOINTS_FILE"
else
    echo "ERROR: Neither $CREDITS_FILE nor $ENDPOINTS_FILE found!" >&2
    exit 1
fi

# Check if update_user_credits function exists
if ! grep -q "def update_user_credits" "$CHECK_FILE"; then
    echo "❌ ERROR: update_user_credits endpoint is missing from $CHECK_FILE" >&2
    echo "This endpoint is REQUIRED and should NOT be removed!" >&2
    echo "Please restore the update_user_credits function." >&2
    echo "" >&2
    echo "To restore from git:" >&2
    echo "  git checkout HEAD -- $CHECK_FILE" >&2
    exit 1
fi

# Check if the route decorator exists (with flexible whitespace matching)
if ! grep -qE '@router\.patch\(["\047]/users/\{user_id\}/credits["\047]\)' "$CHECK_FILE"; then
    echo "❌ ERROR: PATCH /users/{user_id}/credits route is missing from $CHECK_FILE" >&2
    echo "This route is REQUIRED and should NOT be removed!" >&2
    echo "Please restore the @router.patch decorator." >&2
    exit 1
fi

# Check if CreditsUpdate model exists
if ! grep -q "class CreditsUpdate" "$CHECK_FILE"; then
    echo "❌ ERROR: CreditsUpdate model is missing from $CHECK_FILE" >&2
    echo "This model is REQUIRED for the update_user_credits endpoint!" >&2
    exit 1
fi

# Check if security check exists (the secure version)
if ! grep -q "if not current_user.is_superuser" "$CHECK_FILE"; then
    echo "⚠️  WARNING: Security check 'if not current_user.is_superuser' not found!" >&2
    echo "The endpoint may have an insecure permission check." >&2
    echo "Expected: Only superusers should be able to update credits." >&2
    # Don't exit on warning, just warn
fi

echo "✅ All endpoint checks passed"
exit 0
