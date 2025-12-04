# Python Client JWT Authentication Guide

This guide explains how to handle JWT token authentication and expiration when building Python clients for the API.

## JWT Token Overview

The API uses JWT (JSON Web Tokens) for authentication. When you log in, you receive an `access_token` that is valid for **1 hour (3600 seconds)**.

**Important**: The current implementation does not provide refresh tokens. When a token expires, you must re-authenticate by logging in again.

## Token Expiration

### How Token Expiration Works

1. **Token Lifetime**: Access tokens expire after 1 hour (3600 seconds)
2. **Expiration Detection**: The server returns HTTP 401 (Unauthorized) when a token is expired or invalid
3. **No Refresh Endpoint**: There is no `/auth/jwt/refresh` endpoint. You must re-login when the token expires

### Detecting Token Expiration

There are two ways to detect token expiration:

#### Method 1: Check Token Before Request (Recommended)

Decode the JWT token and check its expiration time before making requests:

```python
import jwt
import time
from datetime import datetime

def is_token_expired(token: str) -> bool:
    """Check if JWT token is expired or will expire soon."""
    try:
        # Decode without verification (we only need the payload)
        decoded = jwt.decode(token, options={"verify_signature": False})
        exp = decoded.get('exp')
        if not exp:
            return True

        # Check if token expires in less than 5 minutes (300 seconds)
        current_time = int(time.time())
        time_until_expiration = exp - current_time
        return time_until_expiration < 300
    except Exception:
        return True  # If we can't decode, assume expired
```

#### Method 2: Handle 401 Responses

Catch 401 responses and re-login:

```python
async def make_authenticated_request(client, url, method="GET", **kwargs):
    """Make request and handle token expiration."""
    response = await client.request(method, url, **kwargs)

    if response.status_code == 401:
        # Token expired, need to re-login
        raise TokenExpiredError("Token expired, please re-login")

    return response
```

## Implementation Patterns

### Pattern 1: Check Before Request (Proactive)

```python
import httpx
import jwt
import time
import asyncio

class WebClient:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.client = httpx.AsyncClient(base_url=base_url)
        self.token = None
        self.username = None
        self.password = None

    def is_token_expired(self, token: str) -> bool:
        """Check if token is expired or expiring soon."""
        try:
            decoded = jwt.decode(token, options={"verify_signature": False})
            exp = decoded.get('exp')
            if not exp:
                return True
            current_time = int(time.time())
            return (exp - current_time) < 300  # 5 minutes threshold
        except Exception:
            return True

    async def login(self, username: str, password: str):
        """Login and store credentials for auto re-login."""
        self.username = username
        self.password = password

        response = await self.client.post(
            "/auth/jwt/login",
            data={"username": username, "password": password},
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )

        if response.status_code == 200:
            self.token = response.json()["access_token"]
            print("Login successful")
            return True
        else:
            print(f"Login failed: {response.text}")
            return False

    async def ensure_authenticated(self):
        """Ensure we have a valid token, re-login if needed."""
        if not self.token or self.is_token_expired(self.token):
            if self.username and self.password:
                print("Token expired, re-authenticating...")
                return await self.login(self.username, self.password)
            else:
                raise Exception("Token expired and no credentials available for re-login")
        return True

    async def get_sum(self, a: int, b: int):
        """Make authenticated request with automatic re-login."""
        await self.ensure_authenticated()

        response = await self.client.post(
            "/api/sum",
            json={"a": a, "b": b},
            headers={"Authorization": f"Bearer {self.token}"}
        )

        if response.status_code == 401:
            # Token expired between check and request, try once more
            await self.ensure_authenticated()
            response = await self.client.post(
                "/api/sum",
                json={"a": a, "b": b},
                headers={"Authorization": f"Bearer {self.token}"}
            )

        if response.status_code == 200:
            print(f"Sum result: {response.json()['result']}")
            return response.json()['result']
        else:
            print(f"Sum failed: {response.text}")
            raise Exception(f"Request failed: {response.text}")

    async def close(self):
        await self.client.aclose()

# Usage
async def main():
    client = WebClient()
    await client.login("admin@example.com", "Admin123")

    # Make multiple requests - token will auto-refresh if needed
    await client.get_sum(10, 20)
    await client.get_sum(5, 15)

    await client.close()

if __name__ == "__main__":
    asyncio.run(main())
```

### Pattern 2: Handle 401 Responses (Reactive)

```python
import httpx
import asyncio

class WebClient:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.client = httpx.AsyncClient(base_url=base_url)
        self.token = None
        self.username = None
        self.password = None

    async def login(self, username: str, password: str):
        """Login and store credentials."""
        self.username = username
        self.password = password

        response = await self.client.post(
            "/auth/jwt/login",
            data={"username": username, "password": password},
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )

        if response.status_code == 200:
            self.token = response.json()["access_token"]
            return True
        return False

    async def _make_request_with_retry(self, method: str, url: str, **kwargs):
        """Make request and retry with re-login on 401."""
        if not self.token:
            raise Exception("Not authenticated")

        # Add auth header
        headers = kwargs.get('headers', {})
        headers['Authorization'] = f"Bearer {self.token}"
        kwargs['headers'] = headers

        response = await self.client.request(method, url, **kwargs)

        # If 401, try re-login and retry once
        if response.status_code == 401 and self.username and self.password:
            print("Token expired, re-authenticating...")
            if await self.login(self.username, self.password):
                headers['Authorization'] = f"Bearer {self.token}"
                kwargs['headers'] = headers
                response = await self.client.request(method, url, **kwargs)

        return response

    async def get_sum(self, a: int, b: int):
        """Make authenticated request."""
        response = await self._make_request_with_retry(
            "POST",
            "/api/sum",
            json={"a": a, "b": b}
        )

        if response.status_code == 200:
            return response.json()['result']
        else:
            raise Exception(f"Request failed: {response.text}")

# Usage
async def main():
    client = WebClient()
    await client.login("admin@example.com", "Admin123")

    result = await client.get_sum(10, 20)
    print(f"Sum result: {result}")

    await client.close()
```

## Best Practices

### 1. Store Credentials Securely

**Do NOT** store credentials in plain text in production code. Consider:

- Environment variables
- Secure credential stores (AWS Secrets Manager, HashiCorp Vault, etc.)
- Encrypted configuration files
- User input for interactive scripts

```python
import os

# Good: Use environment variables
username = os.getenv("API_USERNAME")
password = os.getenv("API_PASSWORD")

# Or prompt user
username = input("Username: ")
password = input("Password: ")  # Use getpass for hidden input
```

### 2. Handle Token Expiration Gracefully

Always handle token expiration:

```python
try:
    result = await client.get_sum(10, 20)
except Exception as e:
    if "401" in str(e) or "expired" in str(e).lower():
        # Token expired, handle appropriately
        print("Session expired. Please re-login.")
    else:
        # Other error
        print(f"Error: {e}")
```

### 3. Use Token Expiration Threshold

Check token expiration **before** it expires (e.g., 5 minutes before):

```python
# Refresh token if it expires in less than 5 minutes
if (expiration_time - current_time) < 300:
    # Re-login
    await client.login(username, password)
```

### 4. Implement Request Retry Logic

For long-running scripts, implement retry logic:

```python
async def make_request_with_retry(client, max_retries=2):
    for attempt in range(max_retries):
        try:
            return await client.get_sum(10, 20)
        except TokenExpiredError:
            if attempt < max_retries - 1:
                await client.login(username, password)
                continue
            raise
```

## Dependencies

To decode JWT tokens, you may need the `PyJWT` library:

```bash
pip install PyJWT
```

However, you can also check expiration by making a test request or handling 401 responses without decoding the token.

## Example: Complete Client with Auto Re-login

See `client.py` in this directory for a complete example that implements automatic token refresh through re-login.

## Notes

- **Token Lifetime**: 1 hour (3600 seconds)
- **No Refresh Tokens**: Must re-login when token expires
- **401 Response**: Always indicates expired/invalid token
- **Security**: Never log or expose tokens in production code
