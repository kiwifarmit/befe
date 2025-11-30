/**
 * Tests for Profile.vue component
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createRouter, createWebHistory } from 'vue-router'
import Profile from '../../views/Profile.vue'
import * as auth from '../../utils/auth'

// Mock auth module
vi.mock('../../utils/auth', () => ({
  authenticatedFetch: vi.fn(),
  getCurrentUser: vi.fn(),
}))

// Create a simple router for testing
const createTestRouter = () => {
  return createRouter({
    history: createWebHistory(),
    routes: [
      {
        path: '/profile',
        component: Profile,
        meta: { title: 'Profile' },
      },
      {
        path: '/login',
        component: { template: '<div>Login</div>' },
        meta: { title: 'Login' },
      },
    ],
  })
}

describe('Profile.vue', () => {
  let router
  let wrapper

  beforeEach(() => {
    router = createTestRouter()
    vi.clearAllMocks()
  })

  afterEach(() => {
    if (wrapper) {
      wrapper.unmount()
    }
  })

  const mountProfile = async () => {
    await router.push('/profile')
    wrapper = mount(Profile, {
      global: {
        plugins: [router],
      },
    })
    await wrapper.vm.$nextTick()
    return wrapper
  }

  it('displays user information when loaded', async () => {
    const mockUser = {
      id: '550e8400-e29b-41d4-a716-446655440000',
      email: 'test@example.com',
      credits: 15,
      is_active: true,
      is_verified: true,
    }

    auth.getCurrentUser.mockResolvedValue(mockUser)

    wrapper = await mountProfile()
    await wrapper.vm.$nextTick()

    expect(wrapper.text()).toContain('test@example.com')
    expect(wrapper.text()).toContain('15')
    expect(wrapper.text()).toContain('Active')
    expect(wrapper.text()).toContain('Yes')
  })

  it('shows loading state initially', async () => {
    auth.getCurrentUser.mockImplementation(() => new Promise(() => {})) // Never resolves

    wrapper = await mountProfile()
    await wrapper.vm.$nextTick()

    expect(wrapper.text()).toContain('Loading...')
  })

  it('redirects to login when user data fails to load', async () => {
    auth.getCurrentUser.mockResolvedValue(null)
    const pushSpy = vi.spyOn(router, 'push')

    wrapper = await mountProfile()
    await wrapper.vm.$nextTick()
    await new Promise(resolve => setTimeout(resolve, 100))

    expect(pushSpy).toHaveBeenCalledWith('/login')
  })

  it('displays password update form', async () => {
    const mockUser = {
      id: '550e8400-e29b-41d4-a716-446655440000',
      email: 'test@example.com',
      credits: 15,
      is_active: true,
      is_verified: true,
    }

    auth.getCurrentUser.mockResolvedValue(mockUser)

    wrapper = await mountProfile()
    await wrapper.vm.$nextTick()

    expect(wrapper.find('input[type="password"]').exists()).toBe(true)
    expect(wrapper.text()).toContain('Change Password')
  })

  it('validates password length', async () => {
    const mockUser = {
      id: '550e8400-e29b-41d4-a716-446655440000',
      email: 'test@example.com',
      credits: 15,
      is_active: true,
      is_verified: true,
    }

    auth.getCurrentUser.mockResolvedValue(mockUser)

    wrapper = await mountProfile()
    await wrapper.vm.$nextTick()

    const newPasswordInput = wrapper.find('input#new-password')
    const confirmPasswordInput = wrapper.find('input#confirm-password')
    const form = wrapper.find('form')

    await newPasswordInput.setValue('short')
    await confirmPasswordInput.setValue('short')
    await form.trigger('submit')
    await wrapper.vm.$nextTick()

    expect(wrapper.text()).toContain('at least 8 characters')
  })

  it('validates password match', async () => {
    const mockUser = {
      id: '550e8400-e29b-41d4-a716-446655440000',
      email: 'test@example.com',
      credits: 15,
      is_active: true,
      is_verified: true,
    }

    auth.getCurrentUser.mockResolvedValue(mockUser)

    wrapper = await mountProfile()
    await wrapper.vm.$nextTick()

    const newPasswordInput = wrapper.find('input#new-password')
    const confirmPasswordInput = wrapper.find('input#confirm-password')
    const form = wrapper.find('form')

    await newPasswordInput.setValue('NewPassword123')
    await confirmPasswordInput.setValue('DifferentPassword123')
    await form.trigger('submit')
    await wrapper.vm.$nextTick()

    expect(wrapper.text()).toContain('Passwords do not match')
  })

  it('updates password successfully', async () => {
    const mockUser = {
      id: '550e8400-e29b-41d4-a716-446655440000',
      email: 'test@example.com',
      credits: 15,
      is_active: true,
      is_verified: true,
    }

    auth.getCurrentUser.mockResolvedValue(mockUser)
    auth.authenticatedFetch.mockResolvedValue({
      ok: true,
      json: async () => mockUser,
    })

    wrapper = await mountProfile()
    await wrapper.vm.$nextTick()

    const newPasswordInput = wrapper.find('input#new-password')
    const confirmPasswordInput = wrapper.find('input#confirm-password')
    const form = wrapper.find('form')

    await newPasswordInput.setValue('NewPassword123')
    await confirmPasswordInput.setValue('NewPassword123')
    await form.trigger('submit')
    await wrapper.vm.$nextTick()
    await new Promise(resolve => setTimeout(resolve, 100))

    expect(auth.authenticatedFetch).toHaveBeenCalledWith(
      '/users/me',
      expect.objectContaining({
        method: 'PATCH',
        body: JSON.stringify({ password: 'NewPassword123' }),
      })
    )
    expect(wrapper.text()).toContain('Password updated successfully')
  })

  it('handles password update errors', async () => {
    const mockUser = {
      id: '550e8400-e29b-41d4-a716-446655440000',
      email: 'test@example.com',
      credits: 15,
      is_active: true,
      is_verified: true,
    }

    auth.getCurrentUser.mockResolvedValue(mockUser)
    auth.authenticatedFetch.mockResolvedValue({
      ok: false,
      json: async () => ({ detail: 'Password validation failed' }),
    })

    wrapper = await mountProfile()
    await wrapper.vm.$nextTick()

    const newPasswordInput = wrapper.find('input#new-password')
    const confirmPasswordInput = wrapper.find('input#confirm-password')
    const form = wrapper.find('form')

    await newPasswordInput.setValue('NewPassword123')
    await confirmPasswordInput.setValue('NewPassword123')
    await form.trigger('submit')
    await wrapper.vm.$nextTick()
    await new Promise(resolve => setTimeout(resolve, 100))

    expect(wrapper.text()).toContain('Password validation failed')
  })

  it('redirects to login on token expiration', async () => {
    const mockUser = {
      id: '550e8400-e29b-41d4-a716-446655440000',
      email: 'test@example.com',
      credits: 15,
      is_active: true,
      is_verified: true,
    }

    auth.getCurrentUser.mockResolvedValue(mockUser)
    auth.authenticatedFetch.mockRejectedValue(new Error('TOKEN_EXPIRED'))
    const pushSpy = vi.spyOn(router, 'push')

    wrapper = await mountProfile()
    await wrapper.vm.$nextTick()

    const newPasswordInput = wrapper.find('input#new-password')
    const confirmPasswordInput = wrapper.find('input#confirm-password')
    const form = wrapper.find('form')

    await newPasswordInput.setValue('NewPassword123')
    await confirmPasswordInput.setValue('NewPassword123')
    await form.trigger('submit')
    await wrapper.vm.$nextTick()
    await new Promise(resolve => setTimeout(resolve, 100))

    expect(pushSpy).toHaveBeenCalledWith('/login')
  })

  it('handles user fetch error gracefully', async () => {
    auth.getCurrentUser.mockResolvedValue(null) // getCurrentUser returns null on error
    const pushSpy = vi.spyOn(router, 'push')

    wrapper = await mountProfile()
    await wrapper.vm.$nextTick()
    await new Promise(resolve => setTimeout(resolve, 100))

    expect(pushSpy).toHaveBeenCalledWith('/login')
  })

  it('displays inactive user status', async () => {
    const mockUser = {
      id: '550e8400-e29b-41d4-a716-446655440000',
      email: 'test@example.com',
      credits: 15,
      is_active: false,
      is_verified: true,
    }

    auth.getCurrentUser.mockResolvedValue(mockUser)

    wrapper = await mountProfile()
    await wrapper.vm.$nextTick()

    expect(wrapper.text()).toContain('Inactive')
  })

  it('displays unverified user status', async () => {
    const mockUser = {
      id: '550e8400-e29b-41d4-a716-446655440000',
      email: 'test@example.com',
      credits: 15,
      is_active: true,
      is_verified: false,
    }

    auth.getCurrentUser.mockResolvedValue(mockUser)

    wrapper = await mountProfile()
    await wrapper.vm.$nextTick()

    expect(wrapper.text()).toContain('No')
  })
})

