/**
 * Authentication service for managing JWT tokens
 * Handles token storage, expiration checking, and automatic re-login
 */

const TOKEN_KEY = 'token';
const CREDENTIALS_KEY = 'auth_credentials'; // Store encrypted or hashed credentials if needed
const TOKEN_REFRESH_THRESHOLD = 300; // Refresh token 5 minutes before expiration (in seconds)

/**
 * Decode JWT token without verification (client-side only)
 * @param {string} token - JWT token string
 * @returns {object|null} Decoded token payload or null if invalid
 */
function decodeToken(token) {
  try {
    const base64Url = token.split('.')[1];
    const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
    const jsonPayload = decodeURIComponent(
      atob(base64)
        .split('')
        .map((c) => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2))
        .join('')
    );
    return JSON.parse(jsonPayload);
  } catch (e) {
    return null;
  }
}

/**
 * Check if token is expired or about to expire
 * @param {string} token - JWT token string
 * @returns {boolean} True if token is expired or will expire soon
 */
function isTokenExpiredOrExpiringSoon(token) {
  if (!token) return true;
  
  const decoded = decodeToken(token);
  if (!decoded || !decoded.exp) return true;
  
  const expirationTime = decoded.exp * 1000; // Convert to milliseconds
  const currentTime = Date.now();
  const timeUntilExpiration = (expirationTime - currentTime) / 1000; // Convert to seconds
  
  return timeUntilExpiration < TOKEN_REFRESH_THRESHOLD;
}

/**
 * Get stored access token
 * @returns {string|null} Access token or null
 */
export function getToken() {
  return localStorage.getItem(TOKEN_KEY);
}

/**
 * Store access token
 * @param {string} token - Access token to store
 */
export function setToken(token) {
  localStorage.setItem(TOKEN_KEY, token);
}

/**
 * Remove stored token
 */
export function removeToken() {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(CREDENTIALS_KEY);
}

/**
 * Check if user is authenticated (has valid token)
 * @returns {boolean} True if user has a valid token
 */
export function isAuthenticated() {
  const token = getToken();
  return token && !isTokenExpiredOrExpiringSoon(token);
}

/**
 * Login and store token
 * @param {string} email - User email
 * @param {string} password - User password
 * @returns {Promise<object>} Response data with access_token
 */
export async function login(email, password) {
  const params = new URLSearchParams();
  params.append('username', email);
  params.append('password', password);

  const response = await fetch('/auth/jwt/login', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded',
    },
    body: params,
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: 'Login failed' }));
    throw new Error(errorData.detail || 'Login failed');
  }

  const data = await response.json();
  
  if (data.access_token) {
    setToken(data.access_token);
    // Optionally store credentials for auto re-login (not recommended for production)
    // For now, we'll require manual re-login when token expires
  }
  
  return data;
}

/**
 * Ensure token is valid, attempt re-login if expired
 * Note: Since fastapi-users doesn't provide refresh tokens,
 * we'll need to re-login. This requires stored credentials or user interaction.
 * @returns {Promise<string|null>} Valid token or null if re-login failed
 */
export async function ensureValidToken() {
  const token = getToken();
  
  if (!token) {
    return null;
  }
  
  if (!isTokenExpiredOrExpiringSoon(token)) {
    return token;
  }
  
  // Token is expired or expiring soon
  // Since we don't have refresh tokens, we need to remove the expired token
  // and let the user re-login
  removeToken();
  return null;
}

/**
 * Make authenticated fetch request with automatic token refresh handling
 * @param {string} url - Request URL
 * @param {object} options - Fetch options
 * @returns {Promise<Response>} Fetch response
 */
export async function authenticatedFetch(url, options = {}) {
  let token = await ensureValidToken();
  
  if (!token) {
    // Token expired, need to re-login
    throw new Error('TOKEN_EXPIRED');
  }
  
  const headers = {
    ...options.headers,
    'Authorization': `Bearer ${token}`,
  };
  
  let response = await fetch(url, {
    ...options,
    headers,
  });
  
  // If we get 401, token might have expired between check and request
  if (response.status === 401) {
    removeToken();
    throw new Error('TOKEN_EXPIRED');
  }
  
  return response;
}

/**
 * Logout user
 */
export function logout() {
  removeToken();
}


