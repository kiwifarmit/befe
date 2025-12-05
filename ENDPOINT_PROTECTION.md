# API Endpoint Security Documentation

## Overview

This document describes the security requirements and authorization checks for all API endpoints in the application. All endpoints enforce proper authentication and authorization at both the CRUD/auth level and business logic level.

## Security Rules Summary

1. **Credits Management**: Only superuser can update any user's credits
2. **User CRUD**: Only superuser can GET/PATCH/DELETE other users
3. **Password Changes**: Users can only change their own password via `/users/me/password`
4. **Self-Update**: `PATCH /users/me` is blocked - users must use `/users/me/password` for password changes
5. **Business Logic**: All business endpoints require authentication and validate credits/resources

## Authorization Matrix

| Endpoint | Method | Authentication | Authorization | Notes |
|----------|--------|----------------|---------------|-------|
| `/auth/jwt/login` | POST | None | None | Public endpoint |
| `/auth/register` | POST | None | None | Public endpoint |
| `/auth/forgot-password` | POST | None | None | Public endpoint |
| `/auth/reset-password` | POST | None | None | Requires valid token |
| `/users/me` | GET | Required | Own account | Any authenticated user |
| `/users/me` | PATCH | Required | Blocked | Returns 403 - use `/users/me/password` |
| `/users/me/password` | PATCH | Required | Own account | User can only change own password |
| `/users` | GET | Required | Superuser | Only superusers can list all users |
| `/users/{id}` | GET | Required | Superuser | Only superusers can view other users |
| `/users/{id}` | PATCH | Required | Superuser | Only superusers can update other users |
| `/users/{id}` | DELETE | Required | Superuser | Only superusers can delete users (cannot delete self) |
| `/api/users/{user_id}/credits` | PATCH | Required | Superuser | Only superusers can update credits |
| `/api/sum` | POST | Required | Own account | Requires sufficient credits |

## Endpoint Details

### Authentication Endpoints

#### `POST /auth/jwt/login`
- **Security**: Public (no authentication required)
- **Description**: Authenticate with email and password to receive JWT token
- **Business Logic**: Validates credentials, returns JWT token

#### `POST /auth/register`
- **Security**: Public (no authentication required)
- **Description**: Register a new user account
- **Business Logic**: Validates password strength, creates user with default credits

#### `POST /auth/forgot-password`
- **Security**: Public (no authentication required)
- **Description**: Request password reset token via email
- **Business Logic**: Generates token, sends email (or logs if SMTP not configured)

#### `POST /auth/reset-password`
- **Security**: Public (requires valid reset token)
- **Description**: Reset password using token from email
- **Business Logic**: Validates token, updates password with validation

### User Management Endpoints

#### `GET /users/me`
- **Security**: Authentication required
- **Authorization**: Any authenticated user can access their own profile
- **Description**: Get current user's profile with credits
- **Business Logic**: Loads credits from UserCredits table, creates default if missing

#### `PATCH /users/me`
- **Security**: Authentication required
- **Authorization**: **BLOCKED** - Returns 403 Forbidden
- **Description**: This endpoint is intentionally blocked
- **Reason**: Password changes must use dedicated `/users/me/password` endpoint
- **Response**: `403 Forbidden` with message to use `/users/me/password`

#### `PATCH /users/me/password`
- **Security**: Authentication required
- **Authorization**: User can only change their own password
- **Description**: Change user's own password with current password verification
- **Business Logic**:
  - Verifies current password is correct
  - Validates new password meets requirements (8+ chars, uppercase, lowercase, number)
  - Updates password hash
- **Security Checks**:
  - Current password must be verified
  - New password must meet complexity requirements

#### `GET /users`
- **Security**: Authentication required
- **Authorization**: **Superuser only**
- **Description**: List all users with credits
- **Security Check**: `if not user.is_superuser: raise 403`
- **Business Logic**: Loads all users with their credits

#### `GET /users/{id}`
- **Security**: Authentication required
- **Authorization**: **Superuser only**
- **Description**: Get specific user by ID
- **Security Check**: Uses `current_superuser` dependency
- **Business Logic**: Loads user with credits

#### `PATCH /users/{id}`
- **Security**: Authentication required
- **Authorization**: **Superuser only**
- **Description**: Update user by ID (email, is_active, is_superuser, is_verified, password)
- **Security Check**: Uses `current_superuser` dependency
- **Business Logic**:
  - Validates password if provided
  - Updates all allowed fields
  - Returns updated user with credits

#### `DELETE /users/{id}`
- **Security**: Authentication required
- **Authorization**: **Superuser only**
- **Description**: Delete user by ID
- **Security Checks**:
  - Uses `current_superuser` dependency
  - Prevents self-deletion (`if target_user.id == current_user.id: raise 400`)
- **Business Logic**: Deletes user (cascades to UserCredits if configured)

### Credits Management Endpoints

#### `PATCH /api/users/{user_id}/credits`
- **Security**: Authentication required
- **Authorization**: **Superuser only**
- **Description**: Update user credits
- **Security Check**: `if not current_user.is_superuser: raise 403`
- **Business Logic**:
  - Creates UserCredits if doesn't exist
  - Updates credits value
  - Validates credits >= 0

### Business Logic Endpoints

#### `POST /api/sum`
- **Security**: Authentication required
- **Authorization**: Any authenticated user (own account)
- **Description**: Calculate sum of two numbers, deducting 1 credit
- **Security Checks**:
  - Authentication via `current_active_user` dependency
  - Input validation: `a` and `b` must be between 0 and 1023 (Pydantic Field validation)
- **Business Logic**:
  - Checks user has sufficient credits (>= 1)
  - Calculates result
  - Deducts 1 credit after successful operation
  - Raises 403 if insufficient credits

## Security Implementation Details

### Dependency Helpers

Located in `backend/app/auth.py`:

- `current_active_user`: Requires active authenticated user
- `current_superuser`: Requires active authenticated superuser (raises 403 if not superuser)

### Security Patterns

1. **Superuser Checks**: Use `current_superuser` dependency for admin-only endpoints
2. **Self-Update Restrictions**: Users can only modify their own password via dedicated endpoint
3. **Business Logic Validation**: All business endpoints check credits/resources before operations
4. **Input Validation**: Pydantic models enforce input constraints (ranges, types, etc.)

## Testing Security

All security checks should be tested in `backend/app/tests/test_security.py`:

- Non-superuser cannot access admin endpoints
- Users cannot modify other users
- Users can only change own password
- Business logic constraints (credits, input validation)
- Self-deletion prevention

## Protection Mechanism

The `update_user_credits` endpoint in `backend/app/api/credits.py` is **protected** from accidental removal by a pre-commit hook.

### Pre-commit Hook

1. **Script**: `scripts/check-endpoints.sh` runs automatically before every commit
2. **Validation**: Checks for:
   - `update_user_credits` function
   - `@router.patch("/users/{user_id}/credits")` decorator
   - `CreditsUpdate` model
   - Security check (`if not current_user.is_superuser`)

### If Endpoint Gets Removed

If the endpoint is accidentally removed:

1. **Restore from git**:
   ```bash
   git checkout HEAD -- backend/app/api/credits.py
   ```

2. **Verify it's back**:
   ```bash
   bash scripts/check-endpoints.sh
   ```

## Configuration

- Hook configuration: `.pre-commit-config.yaml`
- Check script: `scripts/check-endpoints.sh`
- Protected file: `backend/app/api/credits.py`
- Excluded from: `autoflake` (won't remove unused imports from this file)

## Troubleshooting

### Hook Not Running?

```bash
# Reinstall pre-commit hooks
source venv/bin/activate
pre-commit install
```

### Bypassing the Hook (NOT RECOMMENDED)

If you absolutely must bypass (e.g., for testing), use:
```bash
git commit --no-verify -m "message"
```

**WARNING**: Only use `--no-verify` if you understand the consequences!
