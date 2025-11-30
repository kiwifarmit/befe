/**
 * Test utilities and helpers
 */

import { vi } from 'vitest'
import { createRouter, createWebHistory } from 'vue-router'

/**
 * Create a mock router for testing
 * @param {Array} routes - Array of route objects
 * @returns {Object} Mock router object
 */
export function createMockRouter(routes = []) {
  const router = createRouter({
    history: createWebHistory(),
    routes: routes.length > 0 ? routes : [
      { path: '/', component: { template: '<div>Home</div>' } },
      { path: '/login', component: { template: '<div>Login</div>' } },
      { path: '/forgot-password', component: { template: '<div>Forgot Password</div>' } },
      { path: '/reset-password', component: { template: '<div>Reset Password</div>' } },
    ],
  })

  return router
}

/**
 * Mock fetch function
 * @param {Object} mockResponse - Mock response object
 * @returns {Function} Mocked fetch function
 */
export function mockFetch(mockResponse) {
  return vi.fn(() =>
    Promise.resolve({
      ok: mockResponse.ok !== undefined ? mockResponse.ok : true,
      status: mockResponse.status || 200,
      statusText: mockResponse.statusText || 'OK',
      json: () => Promise.resolve(mockResponse.data || {}),
      text: () => Promise.resolve(JSON.stringify(mockResponse.data || {})),
    })
  )
}

/**
 * Create a mock token for testing
 * @param {Object} payload - Token payload
 * @returns {string} Mock JWT token
 */
export function createMockToken(payload = {}) {
  const defaultPayload = {
    sub: '550e8400-e29b-41d4-a716-446655440000',
    exp: Math.floor(Date.now() / 1000) + 3600, // 1 hour from now
    ...payload,
  }

  // Simple base64 encoding for testing (not a real JWT)
  const header = btoa(JSON.stringify({ alg: 'HS256', typ: 'JWT' }))
  const body = btoa(JSON.stringify(defaultPayload))
  const signature = btoa('mock-signature')

  return `${header}.${body}.${signature}`
}

/**
 * Mock localStorage helper
 */
export const localStorageMock = {
  store: {},
  getItem: vi.fn((key) => localStorageMock.store[key] || null),
  setItem: vi.fn((key, value) => {
    localStorageMock.store[key] = value.toString()
  }),
  removeItem: vi.fn((key) => {
    delete localStorageMock.store[key]
  }),
  clear: vi.fn(() => {
    localStorageMock.store = {}
  }),
}

/**
 * Reset all mocks
 */
export function resetMocks() {
  vi.clearAllMocks()
  localStorageMock.store = {}
}

