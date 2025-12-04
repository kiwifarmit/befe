# HTTPie API Usage Guide

This guide provides atomic examples for all API endpoints using [HTTPie](https://httpie.io/).

## Prerequisites

Install HTTPie:
```bash
pip install httpie
# or
brew install httpie
```

## Base URL

All examples use `http://localhost:8000` as the base URL. Adjust if your setup differs.

## Authentication

Most endpoints require authentication via JWT Bearer token. After logging in, save the token in a session file for reuse.

---

## Authentication Endpoints

### 1. Login (Get JWT Token)

**Endpoint**: `POST /auth/jwt/login`

**Description**: Authenticate with email and password to receive a JWT access token.

```bash
http --session=./session.json POST http://localhost:8000/auth/jwt/login \
  username=admin@example.com \
  password=Admin123
```

**Response**:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**Note**: The `--session=./session.json` flag saves the token automatically for subsequent requests.

---

### 2. Register New User

**Endpoint**: `POST /auth/register`

**Description**: Register a new user account.

```bash
http POST http://localhost:8000/auth/register \
  email=newuser@example.com \
  password=SecurePass123 \
  is_active:=true \
  is_superuser:=false \
  is_verified:=false
```

**Response**:
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "newuser@example.com",
  "is_active": true,
  "is_superuser": false,
  "is_verified": false
}
```

**Password Requirements**:
- At least 8 characters
- At least one number
- At least one uppercase letter
- At least one lowercase letter

---

### 3. Forgot Password

**Endpoint**: `POST /auth/forgot-password`

**Description**: Request a password reset token via email.

```bash
http POST http://localhost:8000/auth/forgot-password \
  email=user@example.com
```

**Response**:
```json
{
  "detail": "If that email address is in our database, we will send you an email to reset your password."
}
```

**Note**: If SMTP is not configured, the reset token will be logged to `logs/backend.log`.

---

### 4. Reset Password

**Endpoint**: `POST /auth/reset-password`

**Description**: Reset password using the token received via email.

```bash
http POST http://localhost:8000/auth/reset-password \
  token=your-reset-token-here \
  password=NewSecurePass123
```

**Response**:
```json
{
  "detail": "Password updated successfully"
}
```

---

## User Endpoints

### 5. Get Current User Profile

**Endpoint**: `GET /users/me`

**Description**: Get the authenticated user's profile information.

```bash
http --session=./session.json GET http://localhost:8000/users/me
```

**Response**:
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "admin@example.com",
  "is_active": true,
  "is_superuser": true,
  "is_verified": true,
  "credits": 10
}
```

---

### 6. Get User by ID (Admin Only)

**Endpoint**: `GET /users/{id}`

**Description**: Get a specific user's profile by ID. Requires admin privileges.

```bash
http --session=./session.json GET http://localhost:8000/users/550e8400-e29b-41d4-a716-446655440000
```

**Response**:
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "user@example.com",
  "is_active": true,
  "is_superuser": false,
  "is_verified": true,
  "credits": 5
}
```

---

### 7. Update User (Admin Only)

**Endpoint**: `PATCH /users/{id}`

**Description**: Update a user's information. Requires admin privileges.

```bash
http --session=./session.json PATCH http://localhost:8000/users/550e8400-e29b-41d4-a716-446655440000 \
  email:=updated@example.com \
  is_active:=false
```

**Response**:
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "updated@example.com",
  "is_active": false,
  "is_superuser": false,
  "is_verified": true,
  "credits": 5
}
```

**Note**: Only include fields you want to update. Omitted fields remain unchanged.

---

### 8. Delete User (Admin Only)

**Endpoint**: `DELETE /users/{id}`

**Description**: Delete a user account. Requires admin privileges.

```bash
http --session=./session.json DELETE http://localhost:8000/users/550e8400-e29b-41d4-a716-446655440000
```

**Response**: `204 No Content` (empty body)

---

## API Endpoints

### 9. Calculate Sum

**Endpoint**: `POST /api/sum`

**Description**: Calculate the sum of two numbers. Deducts 1 credit from the user's account.

**Authentication**: Required

```bash
http --session=./session.json POST http://localhost:8000/api/sum \
  a:=10 \
  b:=20
```

**Request Body**:
```json
{
  "a": 10,
  "b": 20
}
```

**Response**:
```json
{
  "result": 30
}
```

**Constraints**:
- Both `a` and `b` must be integers between 0 and 1023 (inclusive)
- User must have at least 1 credit
- Each calculation deducts 1 credit from the user's account

**Error Responses**:
- `400 Bad Request`: Invalid input (values outside 0-1023 range)
- `401 Unauthorized`: Missing or invalid authentication token
- `403 Forbidden`: Insufficient credits

---

## Root Endpoint

### 10. Root

**Endpoint**: `GET /`

**Description**: Simple health check endpoint.

```bash
http GET http://localhost:8000/
```

**Response**:
```json
{
  "message": "Hello World"
}
```

---

## Using Session Files

HTTPie session files (e.g., `./session.json`) automatically store and reuse authentication tokens. This eliminates the need to manually include the `Authorization` header in each request.

**Create a new session**:
```bash
http --session=./session.json POST http://localhost:8000/auth/jwt/login \
  username=admin@example.com \
  password=Admin123
```

**Use existing session**:
```bash
http --session=./session.json GET http://localhost:8000/users/me
```

**Use different session files for different users**:
```bash
http --session=./admin.json POST http://localhost:8000/auth/jwt/login \
  username=admin@example.com \
  password=Admin123

http --session=./user.json POST http://localhost:8000/auth/jwt/login \
  username=user@example.com \
  password=User123
```

---

## Error Handling

### Common Error Responses

**401 Unauthorized**:
```json
{
  "detail": "Not authenticated"
}
```

**403 Forbidden**:
```json
{
  "detail": "Insufficient credits. Please contact support to top up."
}
```

**400 Bad Request**:
```json
{
  "detail": "Inputs must be between 0 and 1023"
}
```

**404 Not Found**:
```json
{
  "detail": "Not found"
}
```

---

## Tips

1. **Token Expiration**: JWT tokens expire after 1 hour. Re-login when you receive 401 errors.

2. **JSON vs Form Data**: Use `:=` for JSON numbers/booleans, `=` for strings. For form data (like login), use `=`.

3. **Pretty Print**: HTTPie automatically formats JSON responses. Use `--pretty=all` for even better formatting.

4. **Verbose Output**: Use `-v` or `--verbose` to see request/response headers.

5. **Save Responses**: Use `--download` to save response body to a file.

---

## Complete Workflow Example

```bash
# 1. Login and save token
http --session=./session.json POST http://localhost:8000/auth/jwt/login \
  username=admin@example.com \
  password=Admin123

# 2. Get user profile
http --session=./session.json GET http://localhost:8000/users/me

# 3. Calculate sum (deducts 1 credit)
http --session=./session.json POST http://localhost:8000/api/sum \
  a:=10 \
  b:=20

# 4. Check credits again
http --session=./session.json GET http://localhost:8000/users/me
```
