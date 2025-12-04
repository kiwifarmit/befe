# Endpoint Protection System

## Overview

The `update_user_credits` endpoint in `backend/app/api/endpoints.py` is **protected** from accidental removal by a pre-commit hook.

## Protection Mechanism

1. **Pre-commit Hook**: `scripts/check-endpoints.sh` runs automatically before every commit
2. **Validation**: Checks for:
   - `update_user_credits` function
   - `@router.patch("/users/{user_id}/credits")` decorator
   - `CreditsUpdate` model
   - Security check (`if not current_user.is_superuser`)

## What Happens If Endpoint Is Missing?

If you try to commit without the endpoint, the commit will be **BLOCKED** with:

```
❌ ERROR: update_user_credits endpoint is missing from backend/app/api/endpoints.py
This endpoint is REQUIRED and should NOT be removed!
Please restore the update_user_credits function.
```

## Manual Testing

To test the protection:

```bash
# 1. Verify endpoint exists
grep -c "update_user_credits" backend/app/api/endpoints.py

# 2. Test the hook manually
bash scripts/check-endpoints.sh

# 3. Test with pre-commit
source venv/bin/activate
pre-commit run check-endpoints --all-files
```

## If Endpoint Gets Removed

If the endpoint is accidentally removed:

1. **Restore from git**:
   ```bash
   git checkout HEAD -- backend/app/api/endpoints.py
   ```

2. **Or restore from backup** (if you have one)

3. **Verify it's back**:
   ```bash
   bash scripts/check-endpoints.sh
   ```

## Configuration

- Hook configuration: `.pre-commit-config.yaml`
- Check script: `scripts/check-endpoints.sh`
- Protected file: `backend/app/api/endpoints.py`
- Excluded from: `autoflake` (won't remove unused imports from this file)

## Troubleshooting

### Hook Not Running?

```bash
# Reinstall pre-commit hooks
source venv/bin/activate
pre-commit install
```

### Endpoint Missing After Formatting?

The endpoint is excluded from `autoflake`. If it's still removed:
1. Check your IDE/editor settings for auto-formatting
2. Disable auto-formatting for `backend/app/api/endpoints.py`
3. Use `.gitattributes` to mark it as protected

### Bypassing the Hook (NOT RECOMMENDED)

If you absolutely must bypass (e.g., for testing), use:
```bash
git commit --no-verify -m "message"
```

**WARNING**: Only use `--no-verify` if you understand the consequences!
