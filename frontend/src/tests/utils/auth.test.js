/**
 * Tests for src/utils/auth.js
 */

import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import {
  getToken,
  setToken,
  removeToken,
  isAuthenticated,
  login,
  ensureValidToken,
  authenticatedFetch,
  logout,
} from "../../utils/auth";

// Mock localStorage
const localStorageMock = {
  store: {},
  getItem: vi.fn((key) => localStorageMock.store[key] || null),
  setItem: vi.fn((key, value) => {
    localStorageMock.store[key] = value.toString();
  }),
  removeItem: vi.fn((key) => {
    delete localStorageMock.store[key];
  }),
  clear: vi.fn(() => {
    localStorageMock.store = {};
  }),
};

// Mock global fetch
global.fetch = vi.fn();

// Helper to create a valid JWT token
function createToken(payload = {}) {
  const defaultPayload = {
    sub: "550e8400-e29b-41d4-a716-446655440000",
    exp: Math.floor(Date.now() / 1000) + 3600, // 1 hour from now
    ...payload,
  };
  const header = btoa(JSON.stringify({ alg: "HS256", typ: "JWT" }));
  const body = btoa(JSON.stringify(defaultPayload));
  const signature = btoa("signature");
  return `${header}.${body}.${signature}`;
}

// Helper to create an expired token
function createExpiredToken() {
  const payload = {
    sub: "550e8400-e29b-41d4-a716-446655440000",
    exp: Math.floor(Date.now() / 1000) - 3600, // 1 hour ago
  };
  const header = btoa(JSON.stringify({ alg: "HS256", typ: "JWT" }));
  const body = btoa(JSON.stringify(payload));
  const signature = btoa("signature");
  return `${header}.${body}.${signature}`;
}

// Helper to create a token expiring soon (within 5 minutes)
function createExpiringSoonToken() {
  const payload = {
    sub: "550e8400-e29b-41d4-a716-446655440000",
    exp: Math.floor(Date.now() / 1000) + 200, // 200 seconds from now (less than 300 threshold)
  };
  const header = btoa(JSON.stringify({ alg: "HS256", typ: "JWT" }));
  const body = btoa(JSON.stringify(payload));
  const signature = btoa("signature");
  return `${header}.${body}.${signature}`;
}

beforeEach(() => {
  vi.clearAllMocks();
  localStorageMock.store = {};
  global.localStorage = localStorageMock;
});

afterEach(() => {
  vi.restoreAllMocks();
});

describe("getToken", () => {
  it("should return null when no token is stored", () => {
    expect(getToken()).toBeNull();
  });

  it("should return stored token", () => {
    const token = createToken();
    localStorageMock.store.token = token;
    expect(getToken()).toBe(token);
  });
});

describe("setToken", () => {
  it("should store token in localStorage", () => {
    const token = createToken();
    setToken(token);
    expect(localStorageMock.setItem).toHaveBeenCalledWith("token", token);
    expect(localStorageMock.store.token).toBe(token);
  });
});

describe("removeToken", () => {
  it("should remove token from localStorage", () => {
    localStorageMock.store.token = createToken();
    localStorageMock.store.auth_credentials = "some-credentials";
    removeToken();
    expect(localStorageMock.removeItem).toHaveBeenCalledWith("token");
    expect(localStorageMock.removeItem).toHaveBeenCalledWith(
      "auth_credentials",
    );
    expect(localStorageMock.store.token).toBeUndefined();
  });
});

describe("isAuthenticated", () => {
  it("should return false when no token exists", () => {
    localStorageMock.store = {};
    // isAuthenticated returns token && !isTokenExpiredOrExpiringSoon(token)
    // When token is null, it returns null (falsy), so we check for falsy value
    expect(isAuthenticated()).toBeFalsy();
  });

  it("should return false when token is expired", () => {
    const expiredToken = createExpiredToken();
    localStorageMock.store.token = expiredToken;
    expect(isAuthenticated()).toBe(false);
  });

  it("should return false when token is expiring soon", () => {
    const expiringSoonToken = createExpiringSoonToken();
    localStorageMock.store.token = expiringSoonToken;
    expect(isAuthenticated()).toBe(false);
  });

  it("should return true when token is valid", () => {
    const validToken = createToken();
    localStorageMock.store.token = validToken;
    expect(isAuthenticated()).toBe(true);
  });

  it("should return false when token is invalid format", () => {
    localStorageMock.store.token = "invalid-token";
    expect(isAuthenticated()).toBe(false);
  });
});

describe("login", () => {
  it("should successfully login and store token", async () => {
    const token = createToken();
    const mockResponse = {
      ok: true,
      json: () => Promise.resolve({ access_token: token }),
    };
    global.fetch.mockResolvedValueOnce(mockResponse);

    const result = await login("test@example.com", "password123");

    expect(global.fetch).toHaveBeenCalledWith(
      "/auth/jwt/login",
      expect.objectContaining({
        method: "POST",
        headers: {
          "Content-Type": "application/x-www-form-urlencoded",
        },
      }),
    );
    const callArgs = global.fetch.mock.calls[0];
    expect(callArgs[0]).toBe("/auth/jwt/login");
    expect(callArgs[1].body.toString()).toContain(
      "username=test%40example.com",
    );
    expect(localStorageMock.setItem).toHaveBeenCalledWith("token", token);
    expect(result.access_token).toBe(token);
  });

  it("should throw error on failed login", async () => {
    const mockResponse = {
      ok: false,
      json: () => Promise.resolve({ detail: "Invalid credentials" }),
    };
    global.fetch.mockResolvedValueOnce(mockResponse);

    await expect(login("test@example.com", "wrong-password")).rejects.toThrow(
      "Invalid credentials",
    );
  });

  it("should throw error when response has no detail", async () => {
    const mockResponse = {
      ok: false,
      json: () => Promise.reject(new Error("Parse error")),
    };
    global.fetch.mockResolvedValueOnce(mockResponse);

    await expect(login("test@example.com", "password")).rejects.toThrow(
      "Login failed",
    );
  });
});

describe("ensureValidToken", () => {
  it("should return null when no token exists", async () => {
    const result = await ensureValidToken();
    expect(result).toBeNull();
  });

  it("should return token when valid", async () => {
    const validToken = createToken();
    localStorageMock.store.token = validToken;
    const result = await ensureValidToken();
    expect(result).toBe(validToken);
  });

  it("should remove token and return null when expired", async () => {
    const expiredToken = createExpiredToken();
    localStorageMock.store.token = expiredToken;
    const result = await ensureValidToken();
    expect(result).toBeNull();
    expect(localStorageMock.removeItem).toHaveBeenCalled();
  });

  it("should remove token and return null when expiring soon", async () => {
    const expiringSoonToken = createExpiringSoonToken();
    localStorageMock.store.token = expiringSoonToken;
    const result = await ensureValidToken();
    expect(result).toBeNull();
    expect(localStorageMock.removeItem).toHaveBeenCalled();
  });
});

describe("authenticatedFetch", () => {
  it("should make authenticated request with valid token", async () => {
    const validToken = createToken();
    localStorageMock.store.token = validToken;
    const mockResponse = {
      ok: true,
      status: 200,
      json: () => Promise.resolve({ data: "test" }),
    };
    global.fetch.mockResolvedValueOnce(mockResponse);

    const response = await authenticatedFetch("/api/test");

    expect(global.fetch).toHaveBeenCalledWith("/api/test", {
      headers: {
        Authorization: `Bearer ${validToken}`,
      },
    });
    expect(response).toBe(mockResponse);
  });

  it("should throw TOKEN_EXPIRED when token is invalid", async () => {
    const expiredToken = createExpiredToken();
    localStorageMock.store.token = expiredToken;

    await expect(authenticatedFetch("/api/test")).rejects.toThrow(
      "TOKEN_EXPIRED",
    );
  });

  it("should throw TOKEN_EXPIRED on 401 response", async () => {
    const validToken = createToken();
    localStorageMock.store.token = validToken;
    const mockResponse = {
      ok: false,
      status: 401,
    };
    global.fetch.mockResolvedValueOnce(mockResponse);

    await expect(authenticatedFetch("/api/test")).rejects.toThrow(
      "TOKEN_EXPIRED",
    );
    expect(localStorageMock.removeItem).toHaveBeenCalled();
  });

  it("should pass through custom options", async () => {
    const validToken = createToken();
    localStorageMock.store.token = validToken;
    const mockResponse = {
      ok: true,
      status: 200,
      json: () => Promise.resolve({}),
    };
    global.fetch.mockResolvedValueOnce(mockResponse);

    await authenticatedFetch("/api/test", {
      method: "POST",
      body: JSON.stringify({ test: "data" }),
      headers: { "Custom-Header": "value" },
    });

    expect(global.fetch).toHaveBeenCalledWith("/api/test", {
      method: "POST",
      body: JSON.stringify({ test: "data" }),
      headers: {
        "Custom-Header": "value",
        Authorization: `Bearer ${validToken}`,
      },
    });
  });
});

describe("logout", () => {
  it("should remove token from localStorage", () => {
    localStorageMock.store.token = createToken();
    logout();
    expect(localStorageMock.removeItem).toHaveBeenCalledWith("token");
    expect(localStorageMock.removeItem).toHaveBeenCalledWith(
      "auth_credentials",
    );
  });
});
