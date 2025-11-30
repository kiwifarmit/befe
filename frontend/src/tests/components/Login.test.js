/**
 * Tests for Login.vue component
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createRouter, createWebHistory } from 'vue-router'
import Login from '../../views/Login.vue'
import * as auth from '../../utils/auth'

// Mock auth module
vi.mock('../../utils/auth', () => ({
  login: vi.fn(),
}))

// Mock router
const createTestRouter = () => {
  return createRouter({
    history: createWebHistory(),
    routes: [
      { path: '/', redirect: '/profile' },
      { path: '/profile', component: { template: '<div>Profile</div>' } },
      { path: '/login', component: Login },
      { path: '/forgot-password', component: { template: '<div>Forgot Password</div>' } },
    ],
  })
}

describe('Login.vue', () => {
  let router
  let wrapper

  beforeEach(() => {
    router = createTestRouter()
    vi.clearAllMocks()
  })

  const mountLogin = async () => {
    await router.push('/login')
    wrapper = mount(Login, {
      global: {
        plugins: [router],
      },
    })
    await router.isReady()
    return wrapper
  }

  it('should render login form', async () => {
    wrapper = await mountLogin()
    
    expect(wrapper.find('h2').text()).toBe('Login')
    expect(wrapper.find('input[type="email"]').exists()).toBe(true)
    expect(wrapper.find('input[type="password"]').exists()).toBe(true)
    expect(wrapper.find('button[type="submit"]').exists()).toBe(true)
  })

  it('should bind email input', async () => {
    wrapper = await mountLogin()
    
    const emailInput = wrapper.find('input[type="email"]')
    await emailInput.setValue('test@example.com')
    
    expect(wrapper.vm.email).toBe('test@example.com')
  })

  it('should bind password input', async () => {
    wrapper = await mountLogin()
    
    const passwordInput = wrapper.find('input[type="password"]')
    await passwordInput.setValue('password123')
    
    expect(wrapper.vm.password).toBe('password123')
  })

  it('should call login function on form submit', async () => {
    auth.login.mockResolvedValue({ access_token: 'token123' })
    wrapper = await mountLogin()
    
    await wrapper.find('input[type="email"]').setValue('test@example.com')
    await wrapper.find('input[type="password"]').setValue('password123')
    await wrapper.find('form').trigger('submit.prevent')
    
    expect(auth.login).toHaveBeenCalledWith('test@example.com', 'password123')
  })

  it('should navigate to home on successful login', async () => {
    auth.login.mockResolvedValue({ access_token: 'token123' })
    wrapper = await mountLogin()
    
    await wrapper.find('input[type="email"]').setValue('test@example.com')
    await wrapper.find('input[type="password"]').setValue('password123')
    await wrapper.find('form').trigger('submit.prevent')
    await wrapper.vm.$nextTick()
    await router.isReady()
    // Router navigation happens asynchronously
    await new Promise(resolve => setTimeout(resolve, 100))
    
    expect(router.currentRoute.value.path).toBe('/profile')
  })

  it('should display error message on login failure', async () => {
    auth.login.mockRejectedValue(new Error('Invalid credentials'))
    wrapper = await mountLogin()
    
    await wrapper.find('input[type="email"]').setValue('test@example.com')
    await wrapper.find('input[type="password"]').setValue('wrong-password')
    await wrapper.find('form').trigger('submit.prevent')
    await wrapper.vm.$nextTick()
    
    expect(wrapper.find('.text-red-500').text()).toContain('Invalid credentials')
  })

  it('should clear error message on new submission', async () => {
    auth.login
      .mockRejectedValueOnce(new Error('Invalid credentials'))
      .mockResolvedValueOnce({ access_token: 'token123' })
    wrapper = await mountLogin()
    
    // First failed attempt
    await wrapper.find('input[type="email"]').setValue('test@example.com')
    await wrapper.find('input[type="password"]').setValue('wrong-password')
    await wrapper.find('form').trigger('submit.prevent')
    await wrapper.vm.$nextTick()
    
    expect(wrapper.find('.text-red-500').exists()).toBe(true)
    
    // Second successful attempt
    await wrapper.find('input[type="password"]').setValue('correct-password')
    await wrapper.find('form').trigger('submit.prevent')
    await wrapper.vm.$nextTick()
    
    expect(wrapper.vm.error).toBe('')
  })

  it('should have link to forgot password page', async () => {
    wrapper = await mountLogin()
    
    const forgotPasswordLink = wrapper.find('a[href="/forgot-password"]')
    expect(forgotPasswordLink.exists()).toBe(true)
    expect(forgotPasswordLink.text()).toContain('Forgot Password?')
  })

  it('should have required attributes on inputs', async () => {
    wrapper = await mountLogin()
    
    const emailInput = wrapper.find('input[type="email"]')
    const passwordInput = wrapper.find('input[type="password"]')
    
    expect(emailInput.attributes('required')).toBeDefined()
    expect(passwordInput.attributes('required')).toBeDefined()
    expect(emailInput.attributes('autocomplete')).toBe('email')
    expect(passwordInput.attributes('autocomplete')).toBe('current-password')
  })
})

